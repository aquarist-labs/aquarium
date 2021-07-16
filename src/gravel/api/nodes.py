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
from typing import List, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

from gravel.api import jwt_auth_scheme
from gravel.controllers.nodes.conn import IncomingConnection
from gravel.controllers.nodes.deployment import (
    DeploymentErrorEnum,
    DeploymentState,
    NodeStageEnum,
)
from gravel.controllers.nodes.disks import DiskSolution, Disks
from gravel.controllers.nodes.errors import (
    NodeAlreadyJoiningError,
    NodeCantDeployError,
    NodeError,
    NodeNotDeployedError,
    NodeNotStartedError,
)
from gravel.controllers.nodes.mgr import (
    DeployParamsModel,
    JoinParamsModel,
    NodeMgr,
)


logger: Logger = fastapi_logger
router = APIRouter(prefix="/nodes", tags=["nodes"])


class DeployErrorModel(BaseModel):
    code: DeploymentErrorEnum = Field(
        DeploymentErrorEnum.NONE, title="error code"
    )
    message: Optional[str] = Field(None, title="error message, if possible")


class DeployRequestModel(BaseModel):
    devices: List[str]


class DeployStartReplyModel(BaseModel):
    success: bool = Field(title="operation started successfully")
    error: DeployErrorModel = Field(
        DeployErrorModel(), title="deployment error"
    )


class DeployStatusReplyModel(BaseModel):
    stage: NodeStageEnum = Field(title="current deployment stage")
    progress: int = Field(0, title="deployment progress (percent)")
    error: DeployErrorModel = Field(
        DeployErrorModel(), title="deployment error"
    )


class NodeJoinRequestModel(BaseModel):
    address: str
    token: str
    hostname: str


class TokenReplyModel(BaseModel):
    token: str


class SetHostnameRequest(BaseModel):
    name: str = Field(min_length=1, title="The system hostname")


@router.get("/deployment/disksolution", response_model=DiskSolution)
async def node_get_disk_solution(
    request: Request, _=Depends(jwt_auth_scheme)
) -> DiskSolution:
    """
    Obtain the list of disks and a deployment solution, if possible.
    """
    logger.debug("api > nodes > deployment > devices")
    nodemgr: NodeMgr = request.app.state.nodemgr

    if not nodemgr.available:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="node is not available",
        )

    return Disks.gen_solution(request.app.state.gstate)


@router.post("/deployment/start", response_model=DeployStartReplyModel)
async def node_deploy(
    request: Request, req_params: DeployParamsModel, _=Depends(jwt_auth_scheme)
) -> DeployStartReplyModel:
    """
    Start deploying this node. The host will be configured according to user
    specification; a minimal Ceph cluster will be bootstrapped; and a token for
    other nodes to join the cluster will be generated.

    This is an asynchronous call. The consumer should poll the
    `/nodes/deploy/status` endpoint to gather progress on the operation.
    """
    logger.debug("api > deployment")

    success = True
    error = DeployErrorModel()

    try:
        await request.app.state.nodemgr.deploy(req_params)
    except NodeCantDeployError as e:
        logger.error(f"api > can't deploy: {e.message}")
        success = False
        error = DeployErrorModel(
            code=DeploymentErrorEnum.CANT_BOOTSTRAP, message=e.message
        )
    except NodeNotStartedError as e:
        logger.error("api > node not yet started, can't deploy")
        success = False
        error = DeployErrorModel(
            code=DeploymentErrorEnum.NODE_NOT_STARTED, message=e.message
        )
    except Exception as e:
        logger.exception(e)
        logger.error(f"api > unknown error on deploy: {str(e)}")
        success = False
        error = DeployErrorModel(
            code=DeploymentErrorEnum.UNKNOWN_ERROR, message=str(e)
        )

    if success:
        logger.debug("api > start deployment")

    return DeployStartReplyModel(success=success, error=error)


@router.get("/deployment/status", response_model=DeployStatusReplyModel)
async def get_deployment_status(
    request: Request, _=Depends(jwt_auth_scheme)
) -> DeployStatusReplyModel:
    """
    Get deployment status from this node.

    Provides the current state, and progress if currently deploying or fully
    deployed. Provides error code and message in case it's in an error
    state.

    This information does not survive Aquarium restarts.
    """
    nodemgr: NodeMgr = request.app.state.nodemgr
    state: DeploymentState = nodemgr.deployment_state
    stage: NodeStageEnum = nodemgr.deployment_state.stage

    percent: int = nodemgr.deployment_progress
    return DeployStatusReplyModel(
        stage=stage,
        progress=percent,
        error=DeployErrorModel(
            code=state.error_what.code, message=state.error_what.msg
        ),
    )


@router.post("/deployment/finished", response_model=bool)
async def finish_deployment(
    request: Request, _=Depends(jwt_auth_scheme)
) -> bool:
    """
    Mark a deployment as finished. Triggers internal actions required for node
    operation.
    """
    nodemgr: NodeMgr = request.app.state.nodemgr
    try:
        await nodemgr.finish_deployment()
    except NodeNotDeployedError:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Node has not been deployed",
        )
    except NodeAlreadyJoiningError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Node currently joining an existing cluster",
        )
    except NodeError:
        logger.error("api > unknown error on finished deployment")
        return False
    return True


@router.post("/join")
async def node_join(
    req: NodeJoinRequestModel, request: Request, _=Depends(jwt_auth_scheme)
):
    logger.debug(f"api > join {req.address} with {req.token}")
    if not req.address or not req.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="leader address and token are required",
        )

    nodemgr = request.app.state.nodemgr
    return await nodemgr.join(
        req.address, req.token, JoinParamsModel(hostname=req.hostname)
    )


@router.get("/token", response_model=TokenReplyModel)
async def nodes_get_token(request: Request, _=Depends(jwt_auth_scheme)):
    nodemgr = request.app.state.nodemgr
    token: Optional[str] = nodemgr.token
    return TokenReplyModel(token=(token if token is not None else ""))


router.add_websocket_route(  # pyright: reportUnknownMemberType=false
    "/nodes/ws", IncomingConnection
)
