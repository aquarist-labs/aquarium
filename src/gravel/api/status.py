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
from pathlib import Path
from fastapi.routing import APIRouter
from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field

from gravel.controllers.orch.models import CephStatusModel
from gravel.controllers.resources.status import (
    CephStatusNotAvailableError,
    Status,
    get_status_ctrl
)


logger: Logger = fastapi_logger

router: APIRouter = APIRouter(
    prefix="/status",
    tags=["status"]
)


class StatusModel(BaseModel):
    cluster: Optional[CephStatusModel] = Field(title="cluster status")


@router.get("/", response_model=StatusModel)
async def get_status() -> StatusModel:

    status_ctrl: Status = get_status_ctrl()
    cluster: Optional[CephStatusModel] = None

    try:
        cluster = status_ctrl.status
    except CephStatusNotAvailableError:
        logger.warn("unable to obtain ceph cluster status")
        cluster = None

    status: StatusModel = StatusModel(
        cluster=cluster
    )
    return status


@router.get("/logs")
async def get_logs() -> str:

    logfile: Path = Path("/tmp/aquarium.log")
    if not logfile.exists():
        return ""
    return logfile.read_text()
