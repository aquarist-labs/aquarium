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

from enum import Enum
from logging import Logger
from typing import Optional
from fastapi.routing import APIRouter
from fastapi.logger import logger as fastapi_logger
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from gravel.controllers.nodes.bootstrap import (
    BootstrapStage
)
from gravel.controllers.nodes.mgr import (
    get_node_mgr,
    NodeMgr
)
from gravel.controllers.nodes.errors import (
    NodeAlreadyJoiningError, NodeCantBootstrapError,
    NodeNotBootstrappedError,
    NodeError, NodeNotStartedError
)


logger: Logger = fastapi_logger

router: APIRouter = APIRouter(
    prefix="/bootstrap",
    tags=["bootstrap"]
)


class BootstrapErrorEnum(int, Enum):
    NONE = 0
    CANT_BOOTSTRAP = 1
    NODE_NOT_STARTED = 2
    UNKNOWN_ERROR = 3


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


@router.post("/start", response_model=StartReplyModel)
async def start_bootstrap() -> StartReplyModel:
    """
    Start bootstrapping this node. A minimal Ceph cluster will be deployed on
    the node, and a token, required for other nodes to join, will be generated.

    This is an asynchronous call. The consumer should poll the
    `/bootstrap/status` endpoint to gather progress on the operation.
    """

    success = True
    error = BootstrapErrorModel()

    try:
        await get_node_mgr().bootstrap()
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
        logger.error(f"[API] unknown error on bootstrap: {str(e)}")
        success = False
        error = BootstrapErrorModel(
            code=BootstrapErrorEnum.UNKNOWN_ERROR,
            message=str(e)
        )

    if success:
        logger.debug("[API] start bootstrap")
    return StartReplyModel(success=success, error=error)


@router.get("/status", response_model=StatusReplyModel)
async def get_status() -> StatusReplyModel:
    stage: BootstrapStage = await get_node_mgr().bootstrapper_stage
    percent: int = await get_node_mgr().bootstrapper_progress
    return StatusReplyModel(stage=stage, progress=percent)


@router.post("/finished", response_model=bool)
async def finish_bootstrap() -> bool:
    nodemgr: NodeMgr = get_node_mgr()
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
