# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from logging import Logger
from typing import List
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter
from fastapi import HTTPException, status
from pydantic import BaseModel
from pydantic.fields import Field

from gravel.controllers.services import \
    NotEnoughSpaceError, ServiceError, ServiceModel, \
    ServiceRequirementsModel, ServiceTypeEnum, Services


logger: Logger = fastapi_logger
router: APIRouter = APIRouter(
    prefix="/services",
    tags=["services"]
)


class ReservationsReply(BaseModel):
    reserved: int = Field(0, title="Total reserved storage space (bytes)")


class RequirementsRequest(BaseModel):
    size: int = Field(0, title="Expected storage space (bytes)", gt=0)
    replicas: int = Field(0, title="Number of replicas", gt=0)


class RequirementsReply(BaseModel):
    feasible: bool = Field(False, title="Requested requirements are feasible")
    requirements: ServiceRequirementsModel


class CreateRequest(BaseModel):
    name: str
    type: ServiceTypeEnum
    size: int
    replicas: int


class CreateReply(BaseModel):
    success: bool


@router.get("/reservations", response_model=ReservationsReply)
async def get_reservations() -> ReservationsReply:
    services = Services()
    return ReservationsReply(
        reserved=services.total_reservation
    )


@router.get("/", response_model=List[ServiceModel])
async def get_services() -> List[ServiceModel]:
    services = Services()
    return services.ls()


@router.post("/check-requirements", response_model=RequirementsReply)
async def check_requirements(
    requirements: RequirementsRequest
) -> RequirementsReply:

    size: int = requirements.size
    replicas: int = requirements.replicas

    if size == 0 or replicas == 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="requires positive 'size' and number of 'replicas'"
        )

    services = Services()
    feasible, reqs = services.check_requirements(size, replicas)
    return RequirementsReply(feasible=feasible, requirements=reqs)


@router.post("/create", response_model=CreateReply)
async def create_service(req: CreateRequest) -> CreateReply:

    services = Services()
    try:
        services.create(req.name, req.type, req.size, req.replicas)
    except NotImplementedError:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED,
                            detail="service type not supported")
    except NotEnoughSpaceError:
        raise HTTPException(status.HTTP_507_INSUFFICIENT_STORAGE)
    except ServiceError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))
    return CreateReply(success=True)
