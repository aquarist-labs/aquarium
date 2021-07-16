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

from typing import Any, Dict, List
from pydantic import BaseModel, Field

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


class CephFSListEntryModel(BaseModel):
    name: str
    metadata_pool: str
    metadata_pool_id: int
    data_pool_ids: List[int]
    data_pools: List[str]


class CephFSCapsModel(BaseModel):
    mds: str = Field("", title="mds capabilities")
    mon: str = Field("", title="mon capabilities")
    osd: str = Field("", title="osd capabilities")


class CephFSAuthorizationModel(BaseModel):
    entity: str
    key: str
    caps: CephFSCapsModel


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


class CephOSDDFEntryModel(BaseModel):
    id: int
    device_class: str
    name: str
    type: str
    type_id: int
    crush_weight: float
    depth: int
    pool_weights: Dict[str, Any]
    reweight: int
    kb: int
    kb_used: int
    kb_used_data: int
    kb_used_omap: int
    kb_used_meta: int
    kb_avail: int
    utilization: float
    var: float
    pgs: int
    status: str


class CephOSDDFSummaryModel(BaseModel):
    total_kb: int
    total_kb_used: int
    total_kb_used_data: int
    total_kb_used_meta: int
    total_kb_avail: int
    average_utilization: float
    min_var: float
    max_var: float
    dev: float


class CephOSDDFModel(BaseModel):
    """Result from 'osd df'"""

    nodes: List[CephOSDDFEntryModel]
    stray: List[Any]
    summary: CephOSDDFSummaryModel


class CephOSDPoolEntryModel(BaseModel):
    pool: int
    pool_name: str
    size: int
    min_size: int
    crush_rule: int


class CephOSDMapModel(BaseModel):
    epoch: int
    fsid: str
    flags_set: List[str]
    pools: List[CephOSDPoolEntryModel]


class CephHealthCheckSummaryModel(BaseModel):
    message: str
    count: int


class CephHealthCheckModel(BaseModel):
    severity: str
    summary: CephHealthCheckSummaryModel


class CephHealthStatusModel(BaseModel):
    status: str
    checks: Dict[str, CephHealthCheckModel]


class CephPGStateModel(BaseModel):
    state_name: str
    count: int


class CephPGMapModel(BaseModel):
    pgs_by_state: List[CephPGStateModel]
    num_pgs: int = Field(0, title="Number of placement groups")
    num_pools: int = Field(0, title="Number of pools")
    num_objects: int = Field(0, title="Number of objects")
    # storage statistics
    data_bytes: int = Field(0, title="Total data (byte)")
    bytes_used: int = Field(0, title="Used storage (byte)")
    bytes_avail: int = Field(0, title="Available storage (byte)")
    bytes_total: int = Field(0, title="Total storage (byte)")
    # pg statistics
    inactive_pgs_ratio: float = Field(0, title="Ratio of inactive PGs")
    degraded_objects: int = Field(0, title="Number of degraded objects")
    degraded_total: int = Field(0, title="Total number of degraded copies")
    degraded_ratio: float = Field(0, title="Ratio of degraded objects")
    # client io
    read_bytes_sec: int = Field(0, title="Client reads per second (byte)")
    write_bytes_sec: int = Field(0, title="Client writes per second (byte)")
    read_op_per_sec: int = Field(0, title="Client read operations per second")
    write_op_per_sec: int = Field(0, title="Client write operations per second")


class CephStatusModel(BaseModel):
    fsid: str
    election_epoch: int
    quorum: List[int]
    quorum_names: List[str]
    quorum_age: int
    health: CephHealthStatusModel
    pgmap: CephPGMapModel


class CephOSDPoolRecoveryStatsModel(BaseModel):
    degraded_objects: int = Field(0, title="Number of degraded objects")
    degraded_total: int = Field(0, title="Total number of degraded copies")
    degraded_ratio: float = Field(0, title="Ratio of degraded objects")


class CephOSDPoolClientIORateModel(BaseModel):
    read_bytes_sec: int = Field(0, title="Client reads per second (byte)")
    write_bytes_sec: int = Field(0, title="Client writes per second (byte)")
    read_op_per_sec: int = Field(0, title="Client read operations per second")
    write_op_per_sec: int = Field(0, title="Client write operations per second")


class CephOSDPoolStatsModel(BaseModel):
    pool_name: str
    pool_id: int
    recovery: CephOSDPoolRecoveryStatsModel
    recovery_rate: Dict[str, Any]
    client_io_rate: CephOSDPoolClientIORateModel
