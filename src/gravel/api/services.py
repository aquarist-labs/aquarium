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
from typing import Dict, List, Optional
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter
from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel
from pydantic.fields import Field

from gravel.api import jwt_auth_scheme
from gravel.controllers.orch.cephfs import (
    CephFS,
    CephFSError,
    CephFSNoAuthorizationError,
)
from gravel.controllers.orch.models import CephFSAuthorizationModel
from gravel.controllers.services import (
    ConstraintsModel,
    NotEnoughSpaceError,
    NotReadyError,
    ServiceError,
    ServiceModel,
    ServiceRequirementsModel,
    ServiceStorageModel,
    ServiceTypeEnum,
    UnknownServiceError,
)


logger: Logger = fastapi_logger
router: APIRouter = APIRouter(prefix="/services", tags=["services"])


class RequirementsRequest(BaseModel):
    size: int = Field(0, title="Expected storage space (bytes)", gt=0)
    replicas: int = Field(0, title="Number of replicas", gt=0)


class RequirementsResponse(BaseModel):
    feasible: bool = Field(False, title="Requested requirements are feasible")
    requirements: ServiceRequirementsModel


class CreateRequest(BaseModel):
    name: str
    type: ServiceTypeEnum
    size: int
    replicas: int


class CreateResponse(BaseModel):
    success: bool


@router.get(
    "/constraints",
    name="Obtain service constraints",
    response_model=ConstraintsModel,
)
async def get_constraints(
    request: Request, _=Depends(jwt_auth_scheme)
) -> ConstraintsModel:
    services = request.app.state.gstate.services
    return services.constraints


@router.get("/", response_model=List[ServiceModel])
async def get_services(
    request: Request, _=Depends(jwt_auth_scheme)
) -> List[ServiceModel]:
    services = request.app.state.gstate.services
    return services.ls()


@router.get(
    "/get/{service_name}",
    name="Get service by name",
    response_model=ServiceModel,
)
async def get_service(
    service_name: str, request: Request, _=Depends(jwt_auth_scheme)
) -> ServiceModel:
    services = request.app.state.gstate.services
    try:
        return services.get(service_name)
    except UnknownServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post("/check-requirements", response_model=RequirementsResponse)
async def check_requirements(
    requirements: RequirementsRequest,
    request: Request,
    _=Depends(jwt_auth_scheme),
) -> RequirementsResponse:

    size: int = requirements.size
    replicas: int = requirements.replicas

    if size == 0 or replicas == 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="requires positive 'size' and number of 'replicas'",
        )

    services = request.app.state.gstate.services
    feasible, reqs = services.check_requirements(size, replicas)
    return RequirementsResponse(feasible=feasible, requirements=reqs)


@router.post("/create", response_model=CreateResponse)
async def create_service(
    req: CreateRequest, request: Request, _=Depends(jwt_auth_scheme)
) -> CreateResponse:

    services = request.app.state.gstate.services
    try:
        await services.create(req.name, req.type, req.size, req.replicas)
    except NotImplementedError as e:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except NotEnoughSpaceError:
        raise HTTPException(status.HTTP_507_INSUFFICIENT_STORAGE)
    except ServiceError as e:
        raise HTTPException(
            status.HTTP_428_PRECONDITION_REQUIRED, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    except NotReadyError:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="node not ready yet",
        )
    return CreateResponse(success=True)


@router.get(
    "/stats",
    name="Obtain services statistics",
    response_model=Dict[str, ServiceStorageModel],
)
async def get_statistics(
    request: Request, _=Depends(jwt_auth_scheme)
) -> Dict[str, ServiceStorageModel]:
    """
    Returns a dictionary of service names to a dictionary containing the
    allocated space for said service and how much space is being used, along
    with the service's space utilization.
    """
    services = request.app.state.gstate.services
    try:
        return services.get_stats()
    except NotReadyError:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="node not ready yet",
        )


@router.get(
    "/cephfs/auth/{name}",
    name="Obtain authentication details for a cephfs service",
    response_model=CephFSAuthorizationModel,
)
async def get_authorization(
    request: Request,
    name: str,
    clientid: Optional[str] = None,
    _=Depends(jwt_auth_scheme),
) -> CephFSAuthorizationModel:
    """
    Obtain authorization credentials for a given service `name`. In case of
    success, will return an entity and a cephx key. If `clientid` is supplied,
    will obtain the authorization for a client with said `clientid`, if it
    exists.
    """
    cephfs: CephFS = CephFS(
        request.app.state.gstate.ceph_mgr, request.app.state.gstate.ceph_mon
    )
    try:
        result = cephfs.get_authorization(name, clientid)
        return result
    except CephFSNoAuthorizationError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No authorization found for service",
        )
    except CephFSError as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
