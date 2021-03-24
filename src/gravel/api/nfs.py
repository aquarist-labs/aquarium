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

from fastapi import HTTPException, status
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter

from pydantic import BaseModel

from gravel.controllers.orch.nfs import \
    NFSError, NFSService


logger: Logger = fastapi_logger

router: APIRouter = APIRouter(
    prefix='/nfs',
    tags=['nfs']
)


class ServiceRequest(BaseModel):
    placement: Optional[str] = '*'


class Response(BaseModel):
    detail: str


@router.put(
    '/service/{name}',
    name='create an nfs service',
    response_model=Response)
async def service_create(name: str, req: ServiceRequest) -> Response:
    try:
        res = NFSService().create(name, placement=req.placement)
    except NFSError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))
    return Response(detail=res)


@router.patch(
    '/service/{name}',
    name='update an nfs service',
    response_model=Response)
async def service_update(name: str, req: ServiceRequest) -> Response:
    try:
        res = NFSService().update(name, req.placement if req.placement else '*')
    except NFSError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))
    return Response(detail=res)
