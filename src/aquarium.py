#!/usr/bin/env python3

# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import asyncio
import faulthandler
import logging
import logging.config
import os
import signal
import sys
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.logger import logger as fastapi_logger
from fastapi.staticfiles import StaticFiles

from gravel.api import auth, deploy, devices, local, nodes, orch, status, users
from gravel.cephadm.cephadm import Cephadm
from gravel.controllers.ceph.ceph import Ceph, Mgr, Mon
from gravel.controllers.config import Config
from gravel.controllers.deployment.mgr import (
    DeploymentError,
    DeploymentMgr,
    InitError,
)
from gravel.controllers.gstate import GlobalState, setup_logging
from gravel.controllers.inventory.inventory import Inventory
from gravel.controllers.kv import KV
from gravel.controllers.nodes.mgr import NodeMgr
from gravel.controllers.resources.devices import Devices
from gravel.controllers.resources.network import Network
from gravel.controllers.resources.status import Status
from gravel.controllers.resources.storage import Storage

logger: logging.Logger = fastapi_logger


faulthandler.register(signal.SIGUSR1.value)


def gstate_preinit(gstate: GlobalState) -> None:
    """Things that do not require persistent state to work."""
    # Prep cephadm
    cephadm: Cephadm = Cephadm()
    gstate.add_cephadm(cephadm)
    gstate.preinit()


def gstate_init(gstate: GlobalState, nodemgr: NodeMgr) -> None:
    """Things requiring persistent state to work."""

    gstate.cephadm.set_config(gstate.config.options.containers)

    # Set up Ceph connections
    ceph: Ceph = Ceph()
    ceph_mgr: Mgr = Mgr(ceph)
    gstate.add_ceph_mgr(ceph_mgr)
    ceph_mon: Mon = Mon(ceph)
    gstate.add_ceph_mon(ceph_mon)

    # Set up all of the tickers
    devices: Devices = Devices(
        gstate.config.options.devices.probe_interval,
        nodemgr,
        ceph_mgr,
        ceph_mon,
    )
    gstate.add_devices(devices)

    status: Status = Status(
        gstate.config.options.status.probe_interval, gstate, nodemgr
    )
    gstate.add_status(status)

    inventory: Inventory = Inventory(
        gstate.config.options.inventory.probe_interval, nodemgr, gstate
    )
    gstate.add_inventory(inventory)

    storage: Storage = Storage(
        gstate.config.options.storage.probe_interval, nodemgr, ceph_mon
    )
    gstate.add_storage(storage)

    network: Network = Network(gstate.config.options.network.probe_interval)
    gstate.add_network(network)

    gstate.init()


_shutting_down: bool = False
_main_task: Optional[asyncio.Task] = None


async def aquarium_main_task(
    app: FastAPI,
    config: Config,
    kvstore: KV,
    gstate: GlobalState,
    nodemgr: NodeMgr,
    deployment: DeploymentMgr,
) -> None:
    logger.debug("Starting main Aquarium task.")

    app.state.deployment = deployment

    while not _shutting_down and not deployment.installed:
        logger.debug("Waiting for node to be installed.")
        await asyncio.sleep(1.0)

    if _shutting_down:
        return

    assert deployment.installed

    try:
        await deployment.init()
    except InitError as e:
        logger.error(f"Unable to init node: {e.message}")
        sys.exit(1)

    logger.info("Init Node Manager.")
    config.init()
    kvstore.init()
    gstate_init(gstate, nodemgr)
    nodemgr.init()

    logger.info("Starting Node Manager.")
    await nodemgr.start()
    await gstate.start()

    logger.info("Post-Init Deployment.")
    deployment.postinit(gstate, nodemgr)

    app.state.gstate = gstate
    app.state.nodemgr = nodemgr


async def aquarium_startup(_: FastAPI, aquarium_api: FastAPI):
    lvl = "INFO" if not os.getenv("AQUARIUM_DEBUG") else "DEBUG"
    setup_logging(lvl)
    logger.info("Aquarium startup!")

    deployment = DeploymentMgr()

    try:
        await deployment.preinit()
    except DeploymentError as e:
        logger.error(f"Unable to pre-init the node: {e.message}")
        sys.exit(1)

    config: Config = Config()
    kvstore: KV = KV()
    gstate: GlobalState = GlobalState(config, kvstore)
    nodemgr: NodeMgr = NodeMgr(gstate)

    gstate_preinit(gstate)

    global _main_task
    _main_task = asyncio.create_task(
        aquarium_main_task(
            aquarium_api, config, kvstore, gstate, nodemgr, deployment
        )
    )


async def aquarium_shutdown(_: FastAPI, aquarium_api: FastAPI):
    logger.info("Aquarium shutdown!")

    logger.info("Shutdown main task")
    global _shutting_down, _main_task
    _shutting_down = True
    if _main_task is not None:
        await _main_task

    await aquarium_api.state.gstate.shutdown()
    logger.info("shutting down node manager")
    await aquarium_api.state.nodemgr.shutdown()
    logger.info("Stopping deployment task.")
    await aquarium_api.state.deployment.shutdown()


def aquarium_factory(
    startup_method=aquarium_startup,
    shutdown_method=aquarium_shutdown,
    static_dir=None,
):
    api_tags_metadata = [
        {
            "name": "local",
            "description": "Operations local to the node "
            "where the endpoint is being invoked.",
        },
        {
            "name": "orch",
            "description": "Operations related to Ceph cluster orchestration.",
        },
        {
            "name": "status",
            "description": "Allows obtaining operation status information.",
        },
        {
            "name": "nodes",
            "description": "Perform Aquarium Cluster node operations",
        },
        {
            "name": "devices",
            "description": "Obtain and perform operations on cluster devices",
        },
        {
            "name": "auth",
            "description": "Operations related to user authentication",
        },
        {
            "name": "users",
            "description": "Operations related to user management",
        },
        {
            "name": "deploy",
            "description": "Operations related to the current deployment.",
        },
    ]

    aquarium_app = FastAPI(docs_url=None)
    aquarium_api = FastAPI(
        title="Project Aquarium",
        description="Project Aquarium is a SUSE-sponsored open source project "
        + "aiming at becoming an easy to use, rock solid storage "
        + "appliance based on Ceph.",
        version="1.0.0",
        openapi_tags=api_tags_metadata,
    )

    @aquarium_app.on_event("startup")  # type: ignore
    async def on_startup():
        await startup_method(aquarium_app, aquarium_api)

    @aquarium_app.on_event("shutdown")  # type: ignore
    async def on_shutdown():
        await shutdown_method(aquarium_app, aquarium_api)

    aquarium_api.include_router(local.router)
    aquarium_api.include_router(orch.router)
    aquarium_api.include_router(status.router)
    aquarium_api.include_router(nodes.router)
    aquarium_api.include_router(devices.router)
    aquarium_api.include_router(auth.router)
    aquarium_api.include_router(users.router)
    aquarium_api.include_router(deploy.router)

    #
    # mounts
    #   these should be the last things to be done, so fastapi is aware of
    #   everything that comes before.
    #
    # api calls go here.
    aquarium_app.mount("/api", aquarium_api, name="api")
    # mounting root "/" must be the last thing, so it does not override "/api".
    if static_dir:
        aquarium_app.mount(
            "/", StaticFiles(directory=static_dir, html=True), name="static"
        )

    return aquarium_app


def app_factory():
    static_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "glass/dist/"
    )
    return aquarium_factory(aquarium_startup, aquarium_shutdown, static_dir)


if __name__ == "__main__":
    uvicorn.run("aquarium:app_factory", host="0.0.0.0", port=80, factory=True)
