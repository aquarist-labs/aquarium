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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.logger import logger

from gravel.api.bootstrap import bootstrap
from gravel.api.orch import orch
from gravel.api.status import status


app = FastAPI()
api = FastAPI()


@app.on_event("startup")
async def on_startup():
    uvilogger = logging.getLogger("uvicorn")
    logger.addHandler(uvilogger)
    logger.setLevel(logging.DEBUG)
    logger.info("app startup")
    pass


@app.on_event("shutdown")
async def on_shutdown():
    pass


api.include_router(bootstrap.router)
api.include_router(orch.router)
api.include_router(status.router)


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
