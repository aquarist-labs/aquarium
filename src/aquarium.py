#!/usr/bin/python3

# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import asyncio
import logging
import os
from typing import cast
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.logger import logger as fastapi_logger

from gravel.controllers.gstate import gstate

from gravel.api import bootstrap
from gravel.api import orch
from gravel.api import status
from gravel.api import services
from gravel.api import nodes


logger: logging.Logger = fastapi_logger

app = FastAPI()
api = FastAPI()


@app.on_event("startup")  # type: ignore
async def on_startup():
    uvilogger = cast(logging.Handler, logging.getLogger("uvicorn"))
    logger.addHandler(uvilogger)
    if os.getenv("AQUARIUM_DEBUG"):
        uvilogger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    logger.info("Aquarium startup!")

    # create a task simply so we don't hold up the startup
    asyncio.create_task(gstate.start())
    pass


@app.on_event("shutdown")  # type: ignore
async def on_shutdown():
    await gstate.shutdown()


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
