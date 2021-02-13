# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

from gravel import gstate
from gravel.controllers.config import DeploymentStateModel


router: APIRouter = APIRouter(
    prefix="/status",
    tags=["status"]
)


class StatusModel(BaseModel):
    deployment_state: DeploymentStateModel = Field(title="Deployment State")
    pass


@router.get("/", response_model=StatusModel)
async def get_status() -> StatusModel:
    status: StatusModel = StatusModel(
        deployment_state=gstate.config.deployment_state
    )
    return status
