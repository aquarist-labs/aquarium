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

import asyncio
import logging
import logging.config
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.logger import logger as fastapi_logger

from gravel.controllers.gstate import gstate, setup_logging
from gravel.controllers.nodes import mgr

from gravel.api import bootstrap
from gravel.api import orch
from gravel.api import status
from gravel.api import services
from gravel.api import nodes
from gravel.api import local


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
    }
]


app = FastAPI()
api = FastAPI(openapi_tags=api_tags_metadata)


@app.on_event("startup")  # type: ignore
async def on_startup():

    lvl = "INFO" if not os.getenv("AQUARIUM_DEBUG") else "DEBUG"
    setup_logging(lvl)
    logger.info("Aquarium startup!")

    # init node mgr
    mgr.init_node_mgr()

    # create a task simply so we don't hold up the startup
    asyncio.create_task(gstate.start())
    pass


@app.on_event("shutdown")  # type: ignore
async def on_shutdown():
    await gstate.shutdown()


api.include_router(local.router)
api.include_router(bootstrap.router)
api.include_router(orch.router)
api.include_router(status.router)
api.include_router(services.router)
api.include_router(nodes.router)


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
