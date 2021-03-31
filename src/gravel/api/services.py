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
from fastapi import HTTPException, status
from pydantic import BaseModel
from pydantic.fields import Field
from gravel.controllers.orch.cephfs import (
    CephFS,
    CephFSError,
    CephFSNoAuthorizationError
)
from gravel.controllers.orch.models import CephFSAuthorizationModel

from gravel.controllers.services import (
    ConstraintsModel,
    NotEnoughSpaceError,
    ServiceError,
    ServiceModel,
    ServiceRequirementsModel,
    ServiceStorageModel,
    ServiceTypeEnum,
    Services
)


logger: Logger = fastapi_logger
router: APIRouter = APIRouter(
    prefix="/services",
    tags=["services"]
)


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
    response_model=ConstraintsModel
)
async def get_constraints() -> ConstraintsModel:
    services = Services()
    return services.constraints


@router.get("/", response_model=List[ServiceModel])
async def get_services() -> List[ServiceModel]:
    services = Services()
    return services.ls()


@router.post("/check-requirements", response_model=RequirementsResponse)
async def check_requirements(
    requirements: RequirementsRequest
) -> RequirementsResponse:

    size: int = requirements.size
    replicas: int = requirements.replicas

    if size == 0 or replicas == 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="requires positive 'size' and number of 'replicas'"
        )

    services = Services()
    feasible, reqs = services.check_requirements(size, replicas)
    return RequirementsResponse(feasible=feasible, requirements=reqs)


@router.post("/create", response_model=CreateResponse)
async def create_service(req: CreateRequest) -> CreateResponse:

    services = Services()
    try:
        services.create(req.name, req.type, req.size, req.replicas)
    except NotImplementedError as e:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED,
                            detail=str(e))
    except NotEnoughSpaceError:
        raise HTTPException(status.HTTP_507_INSUFFICIENT_STORAGE)
    except ServiceError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))
    return CreateResponse(success=True)


@router.get(
    "/stats",
    name="Obtain services statistics",
    response_model=Dict[str, ServiceStorageModel]
)
async def get_statistics() -> Dict[str, ServiceStorageModel]:
    """
    Returns a dictionary of service names to a dictionary containing the
    allocated space for said service and how much space is being used, along
    with the service's space utilization.
    """
    services = Services()
    return services.get_stats()


@router.get(
    "/cephfs/auth/{name}",
    name="Obtain authentication details for a cephfs service",
    response_model=CephFSAuthorizationModel
)
async def get_authorization(
    name: str,
    clientid: Optional[str] = None
) -> CephFSAuthorizationModel:
    """
    Obtain authorization credentials for a given service `name`. In case of
    success, will return an entity and a cephx key. If `clientid` is supplied,
    will obtain the authorization for a client with said `clientid`, if it
    exists.
    """
    cephfs: CephFS = CephFS()
    try:
        result = cephfs.get_authorization(name, clientid)
        return result
    except CephFSNoAuthorizationError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No authorization found for service"
        )
    except CephFSError as e:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
