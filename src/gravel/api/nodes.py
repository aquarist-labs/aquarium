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
from fastapi import HTTPException, Request, status
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter
from pydantic.main import BaseModel

from gravel.controllers.nodes.conn import IncomingConnection


logger: Logger = fastapi_logger
router = APIRouter(
    prefix="/nodes",
    tags=["nodes"]
)


class NodeJoinRequestModel(BaseModel):
    address: str
    token: str


class TokenReplyModel(BaseModel):
    token: str


@router.post("/join")
async def node_join(req: NodeJoinRequestModel, request: Request):
    logger.debug(f"api > join {req.address} with {req.token}")
    if not req.address or not req.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="leader address and token are required"
        )

    return await request.app.state.nodemgr.join(req.address, req.token)


@router.get("/token", response_model=TokenReplyModel)
async def nodes_get_token(request: Request):
    nodemgr = request.app.state.nodemgr
    token: Optional[str] = nodemgr.token
    return TokenReplyModel(
        token=(token if token is not None else "")
    )


router.add_websocket_route(  # pyright: reportUnknownMemberType=false
    "/nodes/ws",
    IncomingConnection
)
