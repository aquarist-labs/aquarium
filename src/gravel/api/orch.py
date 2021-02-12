# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from fastapi.routing import APIRouter
from pydantic import BaseModel
from typing import Dict, List
from gravel.cephadm.cephadm import Cephadm
from gravel.cephadm.models import HostFactsModel, VolumeDeviceModel
from gravel.controllers.orch.models import OrchDevicesPerHostModel

from gravel.controllers.orch.orchestrator \
    import OrchestratorDevices, OrchestratorHosts


router: APIRouter = APIRouter(
    prefix="/orch",
    tags=["orch"]
)


class HostModel(BaseModel):
    hostname: str
    address: str


class HostsReplyModel(BaseModel):
    hosts: List[HostModel]


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


@router.get("/hosts", response_model=HostsReplyModel)
def get_hosts() -> HostsReplyModel:
    orch = OrchestratorHosts()
    orch_hosts = orch.ls()
    hosts: HostsReplyModel = HostsReplyModel(hosts=[])
    for h in orch_hosts:
        hosts.hosts.append(HostModel(hostname=h.hostname, address=h.addr))

    return hosts


@router.get("/devices", response_model=Dict[str, HostsDevicesModel])
def get_devices() -> Dict[str, HostsDevicesModel]:
    orch = OrchestratorDevices()
    orch_devs_per_host: List[OrchDevicesPerHostModel] = orch.ls()
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
                    rejected_reasons=dev.rejected_reasons
                )
            )

        host: HostsDevicesModel = HostsDevicesModel(
            address=orch_host.addr,
            hostname=orch_host.name,
            devices=devices
        )
        host_devs[orch_host.name] = host

    return host_devs


@router.get("/facts", response_model=HostFactsModel)
async def get_facts() -> HostFactsModel:
    cephadm = Cephadm()
    return await cephadm.gather_facts()


@router.get("/volumes", response_model=List[VolumeDeviceModel])
async def get_volumes() -> List[VolumeDeviceModel]:
    cephadm = Cephadm()
    return await cephadm.get_volume_inventory()
