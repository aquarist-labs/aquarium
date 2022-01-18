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
from uvicorn import Config as UvicornConfig  # type: ignore
from uvicorn import Server as UvicornServer  # type: ignore

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

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)


class AquariumUvicorn(UvicornServer):
    async def serve(self, sockets=None):
        self._running = True
        await super().serve(sockets)
        self._running = False

    def install_signal_handlers(self) -> None:
        # Do not allow uvicorn to install any signal handlers. We'll handle
        # signals ourselves inside the Aquarium class.
        return


class Aquarium:
    def __init__(self):
        logger.info("Aquarium startup!")

        self._is_shutting_down: bool = False
        self._static_dir: str = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "glass/dist/"
        )

        self.deployment = DeploymentMgr()
        self.config: Config = Config()
        self.kvstore: KV = KV()
        self.cephadm: Cephadm = Cephadm()

        self.gstate: GlobalState = GlobalState(self.config, self.kvstore)
        self.gstate.add_cephadm(self.cephadm)
        self.gstate.preinit()

        self.nodemgr: NodeMgr = NodeMgr(self.gstate)

        self.app = self.app_factory()

    def app_factory(self):
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

        aquarium_api.state.deployment = self.deployment
        aquarium_api.state.gstate = self.gstate
        aquarium_api.state.nodemgr = self.nodemgr

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
        if self._static_dir:
            aquarium_app.mount(
                "/",
                StaticFiles(directory=self._static_dir, html=True),
                name="static",
            )

        return aquarium_app

    async def run(self):
        self.install_signal_handlers()

        await self.bootstrap()
        await self.start_uvicorn()

        await self.main_loop()

        await self.stop_uvicorn()
        await self.shutdown()

    async def bootstrap(self):
        logger.debug("Starting main Aquarium task.")

        try:
            await self.deployment.preinit()
        except DeploymentError as e:
            logger.error(f"Unable to pre-init the node: {e.message}")
            sys.exit(1)

        self.config.init()
        self.kvstore.init()

        self._init_task = asyncio.create_task(self.init())

    async def init(self):
        while not self._is_shutting_down and not self.deployment.installed:
            logger.debug("Waiting for node to be installed.")
            await asyncio.sleep(1.0)

        if self._is_shutting_down:
            return

        assert self.deployment.installed

        try:
            await self.deployment.init()
        except InitError as e:
            logger.error(f"Unable to init node: {e.message}")
            sys.exit(1)

        logger.info("Init Node Manager.")
        self.gstate_init()
        self.nodemgr.init()

        logger.info("Starting Node Manager.")
        await self.nodemgr.start()
        await self.gstate.start()

        logger.info("Post-Init Deployment.")
        self.deployment.postinit(self.gstate, self.nodemgr)

    def gstate_init(self) -> None:
        """Things requiring persistent state to work."""

        self.gstate.cephadm.set_config(self.gstate.config.options.containers)

        # Set up Ceph connections
        ceph: Ceph = Ceph()
        ceph_mgr: Mgr = Mgr(ceph)
        self.gstate.add_ceph_mgr(ceph_mgr)
        ceph_mon: Mon = Mon(ceph)
        self.gstate.add_ceph_mon(ceph_mon)

        # Set up all of the tickers
        devices: Devices = Devices(
            self.gstate.config.options.devices.probe_interval,
            self.nodemgr,
            ceph_mgr,
            ceph_mon,
        )
        self.gstate.add_devices(devices)

        status: Status = Status(
            self.gstate.config.options.status.probe_interval,
            self.gstate,
            self.nodemgr,
        )
        self.gstate.add_status(status)

        inventory: Inventory = Inventory(
            self.gstate.config.options.inventory.probe_interval,
            self.nodemgr,
            self.gstate,
        )
        self.gstate.add_inventory(inventory)

        storage: Storage = Storage(
            self.gstate.config.options.storage.probe_interval,
            self.nodemgr,
            ceph_mon,
        )
        self.gstate.add_storage(storage)

        network: Network = Network(
            self.gstate.config.options.network.probe_interval
        )
        self.gstate.add_network(network)

        self.gstate.init()

    async def main_loop(self):
        while not self._is_shutting_down:
            if self.gstate.requesting_uvicorn_restart:
                await self.restart_uvicorn()
                self.gstate.reset_uvicorn_restart()
            await asyncio.sleep(1)

    async def shutdown(self):
        logger.info("Aquarium shutdown!")
        if self._init_task is not None:
            await self._init_task

        logger.info("shutting down gstate")
        await self.gstate.shutdown()
        logger.info("shutting down node manager")
        await self.nodemgr.shutdown()
        logger.info("Stopping deployment task.")
        await self.deployment.shutdown()

        logger.info("Closing KVStore")
        await self.kvstore.close()

    async def start_uvicorn(self):
        logger.debug("Starting uvicorn")
        if self.gstate.config.options.ssl.use_ssl:
            uvicorn_config = UvicornConfig(
                self.app,
                host="0.0.0.0",
                port=443,
                ssl_keyfile=self.gstate.config.ssl_keypath,
                ssl_certfile=self.gstate.config.ssl_certpath,
            )
        else:
            uvicorn_config = UvicornConfig(self.app, host="0.0.0.0", port=80)
        self.uvicorn = AquariumUvicorn(config=uvicorn_config)
        asyncio.create_task(self.uvicorn.serve())
        # TODO(jhesketh): When in https mode, test if running a second uvicorn
        #                 instance will work to create http redirect.

    async def stop_uvicorn(self):
        logger.debug("Stopping uvicorn")
        self.uvicorn.should_exit = True
        while self.uvicorn._running:
            await asyncio.sleep(0.1)

    async def restart_uvicorn(self):
        logger.debug("Restarting uvicorn")
        await self.stop_uvicorn()
        await self.start_uvicorn()

    def stop(self):
        self._is_shutting_down = True

    def install_signal_handlers(self) -> None:
        loop = asyncio.get_event_loop()
        for sig in HANDLED_SIGNALS:
            loop.add_signal_handler(sig, self.handle_exit, sig, None)

    def handle_exit(self, sig, frame):
        self.stop()


def main():
    lvl = "INFO" if not os.getenv("AQUARIUM_DEBUG") else "DEBUG"
    setup_logging(lvl)

    aqr = Aquarium()
    asyncio.run(aqr.run())
    os._exit(0)


if __name__ == "__main__":
    main()
