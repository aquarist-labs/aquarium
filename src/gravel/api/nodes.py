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

from logging import Logger
from typing import Optional
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter
from pydantic.main import BaseModel

from gravel.controllers.nodes.conn import IncomingConnection
from gravel.controllers.nodes.mgr import get_node_mgr


logger: Logger = fastapi_logger
router = APIRouter(
    prefix="/nodes",
    tags=["nodes"]
)


class TokenReplyModel(BaseModel):
    token: str


@router.post("/join")
async def node_join():
    logger.debug("=> api -- nodes > join")
    return await get_node_mgr().join("127.0.0.1:1337", "foobarbaz")


@router.get("/token", response_model=TokenReplyModel)
async def nodes_get_token():
    nodemgr = get_node_mgr()
    token: Optional[str] = nodemgr.token
    return TokenReplyModel(
        token=(token if token is not None else "")
    )


router.add_websocket_route(  # pyright: reportUnknownMemberType=false
    "/nodes/ws",
    IncomingConnection
)
