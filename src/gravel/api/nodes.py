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
from pydantic.fields import Field
from pydantic.main import BaseModel

from gravel.controllers.nodes.bootstrap import (
    BootstrapErrorEnum,
    BootstrapStage
)

from gravel.controllers.nodes.conn import IncomingConnection
from gravel.controllers.nodes.errors import (
    NodeAlreadyJoiningError,
    NodeCantBootstrapError,
    NodeError,
    NodeNotBootstrappedError,
    NodeNotStartedError
)
from gravel.controllers.nodes.mgr import NodeMgr


logger: Logger = fastapi_logger
router = APIRouter(
    prefix="/nodes",
    tags=["nodes"]
)


class BootstrapErrorModel(BaseModel):
    code: BootstrapErrorEnum = Field(BootstrapErrorEnum.NONE,
                                     title="Error code")
    message: Optional[str] = Field(None, title="Error message, if possible")


class StartReplyModel(BaseModel):
    success: bool = Field(title="Operation started successfully")
    error: BootstrapErrorModel = Field(BootstrapErrorModel(),
                                       title="Bootstrap error")


class StatusReplyModel(BaseModel):
    stage: BootstrapStage = Field(title="Current bootstrapping stage")
    progress: int = Field(0, title="Bootstrap progress (percent)")
    error: BootstrapErrorModel = Field(BootstrapErrorModel(),
                                       title="Bootstrap error")


class NodeJoinRequestModel(BaseModel):
    address: str
    token: str


class TokenReplyModel(BaseModel):
    token: str


router.add_websocket_route(  # pyright: reportUnknownMemberType=false
    "/nodes/ws",
    IncomingConnection
)


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


@router.post("/bootstrap/start", response_model=StartReplyModel)
async def start_bootstrap(request: Request) -> StartReplyModel:
    """
    Start bootstrapping this node. A minimal Ceph cluster will be deployed on
    the node, and a token, required for other nodes to join, will be generated.

    This is an asynchronous call. The consumer should poll the
    `/bootstrap/status` endpoint to gather progress on the operation.
    """

    success = True
    error = BootstrapErrorModel()

    try:
        await request.app.state.nodemgr.bootstrap()
    except NodeCantBootstrapError as e:
        logger.error(f"[API] can't bootstrap: {e.message}")
        success = False
        error = BootstrapErrorModel(
            code=BootstrapErrorEnum.CANT_BOOTSTRAP,
            message=e.message
        )
    except NodeNotStartedError as e:
        logger.error("[API] node not yet started, can't bootstrap")
        success = False
        error = BootstrapErrorModel(
            code=BootstrapErrorEnum.NODE_NOT_STARTED,
            message=e.message
        )
    except Exception as e:
        logger.exception(e)
        logger.error(f"[API] unknown error on bootstrap: {str(e)}")
        success = False
        error = BootstrapErrorModel(
            code=BootstrapErrorEnum.UNKNOWN_ERROR,
            message=str(e)
        )

    if success:
        logger.debug("[API] start bootstrap")
    return StartReplyModel(success=success, error=error)


@router.get("/bootstrap/status", response_model=StatusReplyModel)
async def get_status(request: Request) -> StatusReplyModel:
    """
    Get bootstrapping status from this node.

    Provides the current state, and progress if currently bootstrapping or fully
    bootstrapped. Provides error code and message in case it's in an error
    state.

    This information does not survive Aquarium restarts.
    """
    stage: BootstrapStage = request.app.state.nodemgr.bootstrapper_stage
    percent: int = request.app.state.nodemgr.bootstrapper_progress
    return StatusReplyModel(
        stage=stage,
        progress=percent,
        error=BootstrapErrorModel(
            code=request.app.state.nodemgr.bootstrapper_error_code,
            message=request.app.state.nodemgr.bootstrapper_error_msg
        )
    )


@router.post("/bootstrap/finished", response_model=bool)
async def finish_bootstrap(request: Request) -> bool:
    nodemgr: NodeMgr = request.app.state.nodemgr
    try:
        await nodemgr.finish_deployment()
    except NodeNotBootstrappedError:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Node has not bootstrapped"
        )
    except NodeAlreadyJoiningError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Node currently joining an existing cluster"
        )
    except NodeError:
        logger.error("api > unknown error on finished")
        return False
    return True
