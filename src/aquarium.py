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

import logging
import logging.config
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.logger import logger as fastapi_logger
import uvicorn

from gravel.cephadm.cephadm import Cephadm
from gravel.controllers.gstate import GlobalState, setup_logging
from gravel.controllers.nodes.mgr import NodeMgr
from gravel.controllers.orch.ceph import Ceph, Mgr, Mon
from gravel.controllers.resources.inventory import Inventory
from gravel.controllers.resources.devices import Devices
from gravel.controllers.resources.status import Status
from gravel.controllers.resources.storage import Storage
from gravel.controllers.services import Services

from gravel.api import (
    orch,
    status,
    services,
    nodes,
    local,
    devices,
    nfs,
    auth,
    user,
)

logger: logging.Logger = fastapi_logger


async def aquarium_startup(_: FastAPI, aquarium_api: FastAPI):
    lvl = "INFO" if not os.getenv("AQUARIUM_DEBUG") else "DEBUG"
    setup_logging(lvl)
    logger.info("Aquarium startup!")

    gstate: GlobalState = GlobalState()

    # init node mgr
    logger.info("starting node manager")
    nodemgr: NodeMgr = NodeMgr(gstate)

    # Prep cephadm
    cephadm: Cephadm = Cephadm()
    gstate.add_cephadm(cephadm)

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

    services: Services = Services(
        gstate.config.options.services.probe_interval, gstate, nodemgr
    )
    gstate.add_services(services)

    await nodemgr.start()
    await gstate.start()

    # Add instances into FastAPI's state:
    aquarium_api.state.gstate = gstate
    aquarium_api.state.nodemgr = nodemgr


async def aquarium_shutdown(_: FastAPI, aquarium_api: FastAPI):
    logger.info("Aquarium shutdown!")
    await aquarium_api.state.gstate.shutdown()
    logger.info("shutting down node manager")
    await aquarium_api.state.nodemgr.shutdown()


def aquarium_factory(
    startup_method=aquarium_startup,
    shutdown_method=aquarium_shutdown,
    static_dir=None,
):
    api_tags_metadata = [
        {
            "name": "local",
            "description": "Operations local to the node where the endpoint is being invoked.",
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
            "name": "services",
            "description": "Create, destroy, and operate Aquarium Services.",
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
            "name": "user",
            "description": "Operations related to user management",
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
    aquarium_api.include_router(services.router)
    aquarium_api.include_router(nodes.router)
    aquarium_api.include_router(devices.router)
    aquarium_api.include_router(nfs.router)
    aquarium_api.include_router(auth.router)
    aquarium_api.include_router(user.router)

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
    uvicorn.run("aquarium:app_factory", host="0.0.0.0", port=1337, factory=True)
