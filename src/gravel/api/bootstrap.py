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
    NodeAlreadyJoiningError,
    NodeNotBootstrappedError,
    NodeError
)


logger: Logger = fastapi_logger

router: APIRouter = APIRouter(
    prefix="/bootstrap",
    tags=["bootstrap"]
)


class StartReplyModel(BaseModel):
    success: bool = Field(title="Operation started successfully")


class StatusReplyModel(BaseModel):
    stage: BootstrapStage = Field(title="Current bootstrapping stage")
    progress: int = Field(0, Field="Bootstrap progress (percent)")


@router.post("/start", response_model=StartReplyModel)
async def start_bootstrap() -> StartReplyModel:
    try:
        await get_node_mgr().bootstrap()
    except NodeError as e:
        logger.error(f"api => can't bootstrap: {e.message}")
        return StartReplyModel(success=False)

    logger.debug("api => start bootstrap")
    return StartReplyModel(success=True)


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
