# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from typing import Any, Dict, List
from pydantic import BaseModel


class OrchContainerStatusModel(BaseModel):
    container_image_id: str
    container_image_name: str
    created: str
    last_refresh: str
    running: int
    size: int


class OrchServiceListModel(BaseModel):
    placement: Dict[str, Any]
    service_name: str
    service_type: str
    status: OrchContainerStatusModel


class OrchHostListModel(BaseModel):
    addr: str
    hostname: str
    labels: List[str]
    status: str


class OrchDeviceSysInfoModel(BaseModel):
    human_readable_size: str
    locked: int
    model: str
    nr_requests: str
    partitions: Dict[str, Any]
    removable: str
    rev: str
    ro: str
    rotational: str
    sas_address: str
    sas_device_handle: str
    scheduler_mode: str
    sectors: int
    sectorsize: str
    size: float
    support_discard: str
    vendor: str


class OrchDeviceModel(BaseModel):
    available: bool
    device_id: str
    human_readable_type: str
    lsm_data: Dict[str, Any]
    lvs: List[Any]
    path: str
    rejected_reasons: List[str]
    sys_api: OrchDeviceSysInfoModel


class OrchDevicesPerHostModel(BaseModel):
    addr: str
    devices: List[OrchDeviceModel]
    labels: List[str]
    name: str
