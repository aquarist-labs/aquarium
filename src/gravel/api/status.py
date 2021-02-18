# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from logging import Logger
from typing import Optional
from fastapi.routing import APIRouter
from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field

from gravel.controllers.config import DeploymentStage, DeploymentStateModel
from gravel.controllers.gstate import gstate
from gravel.controllers.orch.ceph import Mon
from gravel.controllers.orch.models import CephStatusModel


logger: Logger = fastapi_logger

router: APIRouter = APIRouter(
    prefix="/status",
    tags=["status"]
)


class StatusModel(BaseModel):
    deployment_state: DeploymentStateModel = Field(title="Deployment State")
    cluster: Optional[CephStatusModel] = Field(title="cluster status")
    pass


@router.get("/", response_model=StatusModel)
async def get_status() -> StatusModel:

    deployment: DeploymentStateModel = gstate.config.deployment_state
    cluster: Optional[CephStatusModel] = None

    if deployment.stage == DeploymentStage.bootstrapped or \
       deployment.stage == DeploymentStage.ready:
        mon = Mon()
        try:
            cluster = mon.status
        except Exception:
            logger.error("unable to obtain cluster status!")
            pass

    status: StatusModel = StatusModel(
        deployment_state=gstate.config.deployment_state,
        cluster=cluster
    )
    return status
