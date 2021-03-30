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

from fastapi import HTTPException, status
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter

from pydantic import BaseModel

from gravel.controllers.orch.nfs import \
    NFSError, NFSBackingStoreEnum, \
    NFSExport, NFSExportModel, \
    NFSService, NFSServiceModel


logger: Logger = fastapi_logger

router: APIRouter = APIRouter(
    prefix='/nfs',
    tags=['nfs']
)


class ServiceRequest(BaseModel):
    placement: Optional[str] = '*'


class ExportRequest(BaseModel):
    binding: str
    fs_type: NFSBackingStoreEnum = NFSBackingStoreEnum.CEPHFS
    fs_name: str
    fs_path: Optional[str]
    readonly: bool = False


class Response(BaseModel):
    detail: str


@router.put(
    '/service/{service_id}',
    name='create an nfs service',
    response_model=Response)
async def service_create(service_id: str, req: ServiceRequest) -> Response:
    try:
        res = NFSService().create(service_id, placement=req.placement)
    except NFSError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))
    return Response(detail=res)


@router.patch(
    '/service/{service_id}',
    name='update an nfs service',
    response_model=Response)
async def service_update(service_id: str, req: ServiceRequest) -> Response:
    try:
        res = NFSService().update(service_id, req.placement if req.placement else '*')
    except NFSError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))
    return Response(detail=res)


@router.delete(
    '/service/{service_id}',
    name='delete an nfs service',
    response_model=Response)
async def service_delete(service_id: str) -> Response:
    try:
        res = NFSService().delete(service_id)
    except NFSError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))
    return Response(detail=res)


@router.get(
    '/service',
    name='list nfs service names',
    response_model=List[str])
def get_service_ls() -> List[str]:
    return NFSService().ls()


@router.get(
    '/service/{service_id}',
    name='nfs service detail',
    response_model=NFSServiceModel)
def get_service_info(service_id: str) -> NFSServiceModel:
    try:
        for svc in NFSService().info(service_id=service_id):
            if svc.service_id == service_id:
                return svc
        raise NFSError(f'unknown nfs service: {service_id}')
    except NFSError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))


@router.post(
    '/export/{service_id}',
    name='create an nfs export',
    response_model=NFSExportModel)
async def export_create(
        service_id: str,
        req: ExportRequest) -> NFSExportModel:
    try:
        res: NFSExportModel = \
            NFSExport().create(
                service_id=service_id,
                binding=req.binding,
                fs_type=req.fs_type,
                fs_name=req.fs_name,
                fs_path=req.fs_path,
                readonly=req.readonly)
    except NFSError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))
    return res


@router.delete(
    '/export/{service_id}/{export_id}',
    name='delete an nfs export',
    response_model=Response)
async def export_delete(service_id: str, export_id: int) -> Response:
    try:
        res = NFSExport().delete(service_id, export_id)
    except NFSError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))
    return Response(detail=res)


@router.get(
    '/export/{service_id}',
    name='list nfs export ids',
    response_model=List[int])
async def get_export_ls(service_id: str) -> List[int]:
    try:
        res = NFSExport().ls(service_id)
    except NFSError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))
    return res


@router.get(
    '/export/{service_id}/{export_id}',
    name='nfs export detail',
    response_model=NFSExportModel)
async def get_export_info(service_id: str, export_id: int) -> NFSExportModel:
    try:
        res = NFSExport().info(service_id)
    except NFSError as e:
        raise HTTPException(status.HTTP_428_PRECONDITION_REQUIRED,
                            detail=str(e))

    for export in res:
        if export.export_id == export_id:
            return export

    raise HTTPException(status.HTTP_404_NOT_FOUND)
