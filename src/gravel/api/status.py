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
from fastapi.routing import APIRouter
from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field

from gravel.controllers.nodes.mgr import (
    NodeMgr,
    NodeStageEnum,
    get_node_mgr
)
from gravel.controllers.orch.ceph import Mon
from gravel.controllers.orch.models import CephStatusModel


logger: Logger = fastapi_logger

router: APIRouter = APIRouter(
    prefix="/status",
    tags=["status"]
)


class StatusModel(BaseModel):
    node_stage: NodeStageEnum = Field(title="Node Deployment Stage")
    cluster: Optional[CephStatusModel] = Field(title="cluster status")
    pass


@router.get("/", response_model=StatusModel)
async def get_status() -> StatusModel:

    nodemgr: NodeMgr = get_node_mgr()
    stage: NodeStageEnum = nodemgr.stage
    cluster: Optional[CephStatusModel] = None

    if stage >= NodeStageEnum.BOOTSTRAPPED and \
       stage != NodeStageEnum.JOINING:
        mon = Mon()
        try:
            cluster = mon.status
        except Exception:
            logger.error("unable to obtain cluster status!")
            pass

    status: StatusModel = StatusModel(
        node_stage=stage,
        cluster=cluster
    )
    return status
