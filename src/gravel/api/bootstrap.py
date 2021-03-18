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

from gravel.controllers.bootstrap import (
    Bootstrap,
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

bootstrap = Bootstrap()


class StartReplyModel(BaseModel):
    success: bool = Field(title="Operation started successfully")


class StatusReplyModel(BaseModel):
    stage: BootstrapStage = Field(title="Current bootstrapping stage")
    progress: int = Field(0, Field="Bootstrap progress (percent)")


@router.post("/start", response_model=StartReplyModel)
async def start_bootstrap() -> StartReplyModel:
    res: bool = await bootstrap.bootstrap()
    logger.debug(f"api > start (success: {res})")
    return StartReplyModel(success=res)


@router.get("/status", response_model=StatusReplyModel)
async def get_status() -> StatusReplyModel:
    stage: BootstrapStage = await bootstrap.get_stage()
    percent: int = await bootstrap.get_progress()
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
