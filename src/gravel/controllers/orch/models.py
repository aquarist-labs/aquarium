# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from typing import Any, Dict, List
from pydantic import BaseModel

from gravel.cephadm.models import VolumeDeviceModel


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


class OrchDevicesPerHostModel(BaseModel):
    addr: str
    devices: List[VolumeDeviceModel]
    labels: List[str]
    name: str


class CephFSNameModel(BaseModel):
    name: str


class CephFSVolumeListModel(BaseModel):
    volumes: List[CephFSNameModel]
