#!/usr/bin/python3

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

from gravel.controllers.gstate import GlobalState, setup_logging
from gravel.controllers.nodes.mgr import NodeMgr
from gravel.controllers.resources.inventory import Inventory
from gravel.controllers.resources.devices import Devices
from gravel.controllers.resources.status import Status
from gravel.controllers.resources.storage import Storage
from gravel.controllers.services import Services

from gravel.api import (
    bootstrap,
    orch,
    status,
    services,
    nodes,
    local,
    devices,
    nfs,
)


logger: logging.Logger = fastapi_logger


api_tags_metadata = [
    {
        "name": "local",
        "description": "Operations local to the node where the endpoint is being invoked."
    },
    {
        "name": "bootstrap",
        "description": "Allows creating a minimal cluster on the node."
    },
    {
        "name": "orch",
        "description": "Operations related to Ceph cluster orchestration."
    },
    {
        "name": "status",
        "description": "Allows obtaining operation status information."
    },
    {
        "name": "services",
        "description": "Create, destroy, and operate Aquarium Services."
    },
    {
        "name": "nodes",
        "description": "Perform Aquarium Cluster node operations"
    },
    {
        "name": "devices",
        "description": "Obtain and perform operations on cluster devices"
    }
]


app = FastAPI(docs_url=None)
api = FastAPI(
    title="Project Aquarium",
    description="Project Aquarium is a SUSE-sponsored open source project " +
                "aiming at becoming an easy to use, rock solid storage " +
                "appliance based on Ceph.",
    version="1.0.0",
    openapi_tags=api_tags_metadata)


@app.on_event("startup")  # type: ignore
async def on_startup():

    lvl = "INFO" if not os.getenv("AQUARIUM_DEBUG") else "DEBUG"
    setup_logging(lvl)
    logger.info("Aquarium startup!")

    gstate: GlobalState = GlobalState()

    # init node mgr
    logger.info("starting node manager")
    nodemgr: NodeMgr = NodeMgr(gstate)

    devices: Devices = Devices(gstate.config.options.devices.probe_interval, nodemgr)
    gstate.add_devices(devices)

    status: Status = Status(gstate.config.options.status.probe_interval, gstate, nodemgr)
    gstate.add_status(status)

    inventory: Inventory = Inventory(gstate.config.options.inventory.probe_interval)
    gstate.add_inventory(inventory)

    storage: Storage = Storage(gstate.config.options.storage.probe_interval, nodemgr)
    gstate.add_storage(storage)

    services: Services = Services(gstate.config.options.services.probe_interval, gstate, nodemgr)
    gstate.add_services(services)

    await nodemgr.start()
    await gstate.start()

    # Add instances into FastAPI's state:
    app.state.gstate = gstate
    app.state.nodemgr = nodemgr


@app.on_event("shutdown")  # type: ignore
async def on_shutdown():
    logger.info("Aquarium shutdown!")
    await app.state.gstate.shutdown()
    logger.info("shutting down node manager")
    await app.state.nodemgr.shutdown()


api.include_router(local.router)
api.include_router(bootstrap.router)
api.include_router(orch.router)
api.include_router(status.router)
api.include_router(services.router)
api.include_router(nodes.router)
api.include_router(devices.router)
api.include_router(nfs.router)


#
# mounts
#   these should be the last things to be done, so fastapi is aware of
#   everything that comes before.
#
# api calls go here.
app.mount(
    "/api",
    api,
    name="api"
)
# mounting root "/" must be the last thing, so it does not override "/api".
app.mount(
    "/",
    StaticFiles(directory="./glass/dist/", html=True),
    name="static"
)
