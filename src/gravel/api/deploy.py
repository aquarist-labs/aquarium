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
from typing import Any, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

from gravel.api import jwt_auth_scheme, install_gate
from gravel.controllers.deployment.create import ContainerConfig
from gravel.controllers.deployment.mgr import (
    DeploymentError,
    DeploymentMgr,
    DeploymentStateEnum,
    DeploymentStatusModel,
    NodeDeployedError,
    NodeInstalledError,
    NotPostInitedError,
)
from gravel.controllers.inventory.disks import DiskDevice
from gravel.controllers.nodes.requirements import (
    RequirementsModel,
)

logger: Logger = fastapi_logger
router: APIRouter = APIRouter(prefix="/deploy", tags=["deploy"])


class DeployStatusReplyModel(BaseModel):
    installed: bool = Field(title="Node has been installed.")
    status: DeploymentStatusModel = Field(title="Deployment status.")


class DeployInstallReplyModel(BaseModel):
    state: DeploymentStateEnum = Field(title="Deployment state.")


class DeployInstallParamsModel(BaseModel):
    device: str = Field("Device to install on.")


class DeployRequirementsReplyModel(BaseModel):
    requirements: RequirementsModel


class DeployDevicesReplyModel(BaseModel):
    devices: List[DiskDevice]


class RegistryParamsModel(BaseModel):
    registry: str = Field(title="Registry URL.")
    secure: bool = Field(title="Whether registry is secure.")
    image: str = Field(title="Image to use.")


class CreateParamsModel(BaseModel):
    hostname: str = Field(title="Hostname to use for this node.")
    ntpaddr: str = Field(title="NTP address to be used.")
    registry: Optional[RegistryParamsModel] = Field(
        None, title="Custom registry."
    )
    storage: List[str] = Field([], title="Devices to be consumed for storage.")


def _get_status(dep: DeploymentMgr) -> DeployStatusReplyModel:
    return DeployStatusReplyModel(
        installed=dep.installed, status=dep.get_status()
    )


@router.get("/status", response_model=DeployStatusReplyModel)
async def deploy_status(
    request: Request, _=Depends(jwt_auth_scheme)
) -> DeployStatusReplyModel:
    """Obtain the status of this node's deployment."""
    return _get_status(request.app.state.deployment)


@router.post("/install", response_model=DeployInstallReplyModel)
async def deploy_install(
    request: Request,
    params: DeployInstallParamsModel,
    _=Depends(jwt_auth_scheme),
) -> DeployInstallReplyModel:
    """Start installing this node."""

    dep: DeploymentMgr = request.app.state.deployment
    try:
        await dep.install(params.device)
    except NodeInstalledError:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Node already installed.",
        )
    return DeployInstallReplyModel(
        state=dep.state,
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


@router.post("/create", response_model=DeployStatusReplyModel)
async def deploy_create(
    request: Request,
    params: CreateParamsModel,
    jwt: Any = Depends(jwt_auth_scheme),
    gate: Any = Depends(install_gate),
) -> DeployStatusReplyModel:
    """
    Create a new deployment on this node.

    The host will be configured according to the user's specification.
    A minimal Ceph cluster will be created.

    This is an asynchronous call. The consumer should poll '/deploy/status' to
    gather progress on the operation.
    """
    logger.debug("Create new deployment.")
    dep: DeploymentMgr = request.app.state.deployment
    try:
        ctrcfg: Optional[ContainerConfig] = None
        if params.registry is not None:
            ctrcfg = ContainerConfig(
                url=params.registry.registry,
                image=params.registry.image,
                secure=params.registry.secure,
            )
        await dep.create(
            params.hostname, params.ntpaddr, ctrcfg, params.storage
        )
    except (NotPostInitedError, NodeDeployedError) as e:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=e.message
        )
    except DeploymentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        )
    return _get_status(dep)
