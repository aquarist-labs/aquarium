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
from fastapi.routing import APIRouter
from fastapi.logger import logger as fastapi_logger
from fastapi import Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Dict, List

from gravel.api import jwt_auth_scheme
from gravel.controllers.orch.models import OrchDevicesPerHostModel
from gravel.controllers.orch.orchestrator import Orchestrator


logger: Logger = fastapi_logger

router: APIRouter = APIRouter(prefix="/orch", tags=["orch"])


class HostModel(BaseModel):
    hostname: str
    address: str


class DeviceModel(BaseModel):
    available: bool
    device_id: str
    model: str
    vendor: str
    human_readable_type: str
    size: int
    path: str
    rejected_reasons: List[str]


class HostsDevicesModel(BaseModel):
    address: str
    hostname: str
    devices: List[DeviceModel]


@router.get("/hosts", response_model=List[HostModel])
def get_hosts(request: Request, _=Depends(jwt_auth_scheme)) -> List[HostModel]:
    orch = Orchestrator(request.app.state.gstate.ceph_mgr)
    orch_hosts = orch.host_ls()
    hosts: List[HostModel] = []
    for h in orch_hosts:
        hosts.append(HostModel(hostname=h.hostname, address=h.addr))
    return hosts


@router.get("/devices", response_model=Dict[str, HostsDevicesModel])
def get_devices(
    request: Request, _=Depends(jwt_auth_scheme)
) -> Dict[str, HostsDevicesModel]:
    orch = Orchestrator(request.app.state.gstate.ceph_mgr)
    orch_devs_per_host: List[OrchDevicesPerHostModel] = orch.devices_ls()
    host_devs: Dict[str, HostsDevicesModel] = {}
    for orch_host in orch_devs_per_host:

        devices: List[DeviceModel] = []
        for dev in orch_host.devices:
            devices.append(
                DeviceModel(
                    available=dev.available,
                    device_id=dev.device_id,
                    model=dev.sys_api.model,
                    vendor=dev.sys_api.vendor,
                    human_readable_type=dev.human_readable_type,
                    size=int(dev.sys_api.size),
                    path=dev.path,
                    rejected_reasons=dev.rejected_reasons,
                )
            )

        host: HostsDevicesModel = HostsDevicesModel(
            address=orch_host.addr, hostname=orch_host.name, devices=devices
        )
        host_devs[orch_host.name] = host

    return host_devs


@router.get("/pubkey")
async def get_pubkey(request: Request, _=Depends(jwt_auth_scheme)) -> str:
    try:
        orch = Orchestrator(request.app.state.gstate.ceph_mgr)
        return orch.get_public_key()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
