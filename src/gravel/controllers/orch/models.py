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


class CephDFStatsBaseModel(BaseModel):
    total_bytes: int
    total_avail_bytes: int
    total_used_bytes: int
    total_used_raw_bytes: int
    total_used_raw_ratio: float


class CephDFStatsModel(CephDFStatsBaseModel):
    num_osds: int
    num_per_pool_osds: int
    num_per_pool_omap_osds: int


class CephDFPoolStatsModel(BaseModel):
    stored: int
    objects: int
    kb_used: int
    bytes_used: int
    percent_used: float
    max_avail: int


class CephDFPoolModel(BaseModel):
    name: str
    id: int
    stats: CephDFPoolStatsModel


class CephDFModel(BaseModel):
    stats: CephDFStatsModel
    stats_by_class: Dict[str, CephDFStatsBaseModel]
    pools: List[CephDFPoolModel]


class CephOSDPoolEntryModel(BaseModel):
    pool: int
    pool_name: str
    size: int
    min_size: int


class CephOSDMapModel(BaseModel):
    epoch: int
    fsid: str
    flags_set: List[str]
    pools: List[CephOSDPoolEntryModel]
