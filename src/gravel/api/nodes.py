# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from logging import Logger
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter

from gravel.controllers.nodes import IncomingConnection, get_node_mgr


logger: Logger = fastapi_logger
router = APIRouter(
    prefix="/nodes",
    tags=["nodes"]
)


@router.post("/join")
async def node_join():
    logger.debug("=> api -- nodes > join")
    return await get_node_mgr().join("127.0.0.1:1337", "foobarbaz")


router.add_websocket_route(  # pyright: reportUnknownMemberType=false
    "/nodes/ws",
    IncomingConnection
)
