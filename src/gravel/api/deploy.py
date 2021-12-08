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

from gravel.api import install_gate, jwt_auth_scheme
from gravel.controllers.deployment.create import ContainerConfig
from gravel.controllers.deployment.join import (
    AlreadyJoinedError,
    BadTokenError,
    HostnameExistsError,
    JoinError,
    JoinReadyParamsModel,
    JoinReadyReplyModel,
    JoinRequestParamsModel,
    JoinRequestReplyModel,
)
from gravel.controllers.deployment.mgr import (
    DeploymentError,
    DeploymentMgr,
    DeploymentStatusModel,
    NodeDeployedError,
    NodeInstalledError,
    NodeUnrecoverableError,
    NotPostInitedError,
    NotReadyYetError,
    ParamsError,
)
from gravel.controllers.inventory.disks import DiskDevice
from gravel.controllers.nodes.requirements import RequirementsModel
from gravel.controllers.resources.network import NetworkConfigModel

logger: Logger = fastapi_logger
router: APIRouter = APIRouter(prefix="/deploy", tags=["deploy"])


class PostDeploymentGateKeeper:
    def __init__(self):
        pass

    def __call__(self, request: Request) -> None:
        dep: DeploymentMgr = request.app.state.deployment
        if dep.deployed:
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Method not available after node deployment.",
            )


postdep_gate = PostDeploymentGateKeeper()


class DeployStatusReplyModel(BaseModel):
    installed: bool = Field(title="Node has been installed.")
    status: DeploymentStatusModel = Field(title="Deployment status.")


class DeployInstallReplyModel(BaseModel):
    success: bool = Field(title="Whether the operation request was successful.")


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
    network: Optional[NetworkConfigModel] = Field(
        None, title="Network configuration."
    )
    storage: List[str] = Field([], title="Devices to be consumed for storage.")


class DeployTokenReplyModel(BaseModel):
    token: str = Field(title="The cluster token, required to join.")


class JoinParamsModel(BaseModel):
    address: str = Field(title="Address of node to contact.")
    token: str = Field(title="Token to join the cluster.")
    hostname: str = Field(title="Hostname to use when joining.")
    storage: List[str] = Field(title="Devices to be used for storage.")
    network: Optional[NetworkConfigModel] = Field(
        title="Network configuration."
    )


class JoinReplyModel(BaseModel):
    success: bool = Field(title="Whether the request was successful.")
    msg: str = Field(title="A response message, if any.")


def _get_status(dep: DeploymentMgr) -> DeployStatusReplyModel:
    return DeployStatusReplyModel(
        installed=dep.installed, status=dep.get_status()
    )


@router.get("/status", response_model=DeployStatusReplyModel)
async def deploy_status(request: Request) -> DeployStatusReplyModel:
    """Obtain the status of this node's deployment."""
    return _get_status(request.app.state.deployment)


@router.post("/install", response_model=DeployInstallReplyModel)
async def deploy_install(
    request: Request,
    params: DeployInstallParamsModel,
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
    return DeployInstallReplyModel(success=True)


@router.get("/requirements", response_model=DeployRequirementsReplyModel)
async def deploy_requirements(
    request: Request,
    postdep: Any = Depends(postdep_gate),
) -> DeployRequirementsReplyModel:
    """Obtain system requirements for install."""
    dep: DeploymentMgr = request.app.state.deployment
    req = await dep.get_requirements()
    return DeployRequirementsReplyModel(
        requirements=req,
    )


@router.get("/devices", response_model=DeployDevicesReplyModel)
async def deploy_devices(
    request: Request,
    postdep: Any = Depends(postdep_gate),
) -> DeployDevicesReplyModel:
    """Obtain storage devices."""
    dep: DeploymentMgr = request.app.state.deployment
    devs = await dep.get_devices()
    return DeployDevicesReplyModel(devices=devs)


@router.post("/create", response_model=DeployStatusReplyModel)
async def deploy_create(
    request: Request,
    params: CreateParamsModel,
    install: Any = Depends(install_gate),
    postdep: Any = Depends(postdep_gate),
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
            params.hostname,
            params.ntpaddr,
            ctrcfg,
            params.network,
            params.storage,
        )
    except (NotPostInitedError, NodeDeployedError) as e:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=e.message
        )
    except NodeUnrecoverableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    except DeploymentError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.message
        )
    return _get_status(dep)


@router.get("/token", response_model=DeployTokenReplyModel)
async def get_token(
    request: Request,
    install_gate: Any = Depends(install_gate),
    jwt_gate: Any = Depends(jwt_auth_scheme),
) -> DeployTokenReplyModel:
    """Obtain the cluster token"""
    dep: DeploymentMgr = request.app.state.deployment
    try:
        token = await dep.get_token()
    except NotReadyYetError as e:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=e.message
        )
    return DeployTokenReplyModel(token=token)


@router.post("/join", response_model=JoinReplyModel)
async def deploy_join(
    request: Request,
    params: JoinParamsModel,
    install: Any = Depends(install_gate),
    postdep: Any = Depends(postdep_gate),
) -> JoinReplyModel:
    """
    Start joining an existing cluster.

    This endpoint should be called on the node wanting to join, with
    information specifying which node to contact.
    """
    remote_addr: str = params.address.strip()
    token: str = params.token.strip()
    hostname: str = params.hostname.strip()
    storage: List[str] = params.storage
    network: Optional[NetworkConfigModel] = params.network

    logger.debug(f"Join existing deployment at {remote_addr}")
    dep: DeploymentMgr = request.app.state.deployment
    try:
        await dep.join(remote_addr, token, hostname, network, storage)
    except (NotPostInitedError, NodeDeployedError) as e:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=e.message
        )
    except NodeUnrecoverableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    except ParamsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return JoinReplyModel(success=True, msg="")


@router.post("/join/request", response_model=JoinRequestReplyModel)
async def deploy_join_request(
    request: Request,
    params: JoinRequestParamsModel,
    gate: Any = Depends(install_gate),
) -> JoinRequestReplyModel:
    """
    Request from another node to join our existing cluster.

    This endpoint should be called from a node outside the cluster and wanting
    to join our existing cluster. If we are not part of a cluster, an error
    should be returned to the caller.
    """
    logger.debug(f"Join Request: {params}")
    hostname = params.hostname.strip()
    addr = params.address.strip()
    token = params.token.strip()

    if not hostname or not addr or not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    dep: DeploymentMgr = request.app.state.deployment
    try:
        reply = await dep.handle_join_request(
            params.uuid, hostname, addr, token
        )
    except NotReadyYetError as e:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=e.message
        )
    except BadTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad token."
        )
    except (HostnameExistsError, AlreadyJoinedError) as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        )
    except JoinError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        )
    return reply


@router.post("/join/ready", response_model=JoinReadyReplyModel)
async def deploy_join_ready(
    request: Request,
    params: JoinReadyParamsModel,
    gate: Any = Depends(install_gate),
) -> JoinReadyReplyModel:
    """
    Acknowledgement from another node that they are ready to be added to the
    cluster.
    """
    logger.debug(f"Join Ready for UUID {params.uuid}")
    uuid = params.uuid

    dep: DeploymentMgr = request.app.state.deployment
    try:
        await dep.handle_join_ready(uuid)
    except HostnameExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        )
    except JoinError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message
        )

    return JoinReadyReplyModel(success=True, msg="")
