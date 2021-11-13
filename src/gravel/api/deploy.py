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
from typing import List

from fastapi import Depends, HTTPException, Request, status
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

from gravel.api import jwt_auth_scheme
from gravel.controllers.deployment.mgr import DeploymentMgr, DeploymentStateEnum
from gravel.controllers.inventory.disks import DiskDevice
from gravel.controllers.nodes.requirements import (
    RequirementsModel,
)

logger: Logger = fastapi_logger
router: APIRouter = APIRouter(prefix="/deploy", tags=["deploy"])


class DeployStatusReplyModel(BaseModel):
    installed: bool = Field(title="Node has been installed.")
    state: DeploymentStateEnum = Field(title="Deployment state.")


class DeployInstallReplyModel(BaseModel):
    state: DeploymentStateEnum = Field(title="Deployment state.")


class DeployInstallParamsModel(BaseModel):
    device: str = Field("Device to install on.")


class DeployRequirementsReplyModel(BaseModel):
    requirements: RequirementsModel


class DeployDevicesReplyModel(BaseModel):
    devices: List[DiskDevice]


@router.get("/status", response_model=DeployStatusReplyModel)
async def deploy_status(
    request: Request, _=Depends(jwt_auth_scheme)
) -> DeployStatusReplyModel:
    """Obtain the status of this node's deployment."""

    dep: DeploymentMgr = request.app.state.deployment
    return DeployStatusReplyModel(
        installed=dep.installed,
        state=dep.state,
    )


@router.post("/install", response_model=DeployInstallReplyModel)
async def deploy_install(
    request: Request,
    params: DeployInstallParamsModel,
    _=Depends(jwt_auth_scheme),
) -> DeployInstallReplyModel:
    """Start installing this node."""
    return DeployInstallReplyModel(
        state=DeploymentStateEnum.NONE,
    )


@router.get("/requirements", response_model=DeployRequirementsReplyModel)
async def deploy_requirements(
    request: Request,
    _=Depends(jwt_auth_scheme),
) -> DeployRequirementsReplyModel:
    """Obtain system requirements for install."""
    dep: DeploymentMgr = request.app.state.deployment
    req = await dep.get_requirements()
    return DeployRequirementsReplyModel(
        requirements=req,
    )


@router.get("/devices", response_model=DeployDevicesReplyModel)
async def deploy_devices(
    request: Request, _=Depends(jwt_auth_scheme)
) -> DeployDevicesReplyModel:
    """Obtain storage devices."""
    dep: DeploymentMgr = request.app.state.deployment
    devs = await dep.get_devices()
    return DeployDevicesReplyModel(devices=devs)
