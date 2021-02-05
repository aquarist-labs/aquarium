# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from fastapi.routing import APIRouter
from fastapi.logger import logger
from pydantic import BaseModel, Field

from gravel.controllers.bootstrap \
    import Bootstrap, BootstrapStage

router: APIRouter = APIRouter(
    prefix="/bootstrap",
    tags=["bootstrap"]
)

bootstrap = Bootstrap()


class StartReplyModel(BaseModel):
    success: bool = Field(title="Operation started successfully")


class StatusReplyModel(BaseModel):
    stage: BootstrapStage = Field(title="Current bootstrapping stage")


@router.post("/start", response_model=StartReplyModel)
async def start_bootstrap() -> StartReplyModel:
    res: bool = await bootstrap.bootstrap()
    logger.info(f"bootstrap > start (success: {res})")
    return StartReplyModel(success=res)


@router.get("/status", response_model=StatusReplyModel)
async def get_status() -> StatusReplyModel:
    stage: BootstrapStage = await bootstrap.get_stage()
    return StatusReplyModel(stage=stage)
