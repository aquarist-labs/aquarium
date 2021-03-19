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
from pydantic import BaseModel
from pydantic.fields import Field


class DeviceModel(BaseModel):
    description: str
    dev_name: str
    disk_size_bytes: int
    model: str
    rev: str
    vendor: str
    wwid: str


class NICModel(BaseModel):
    driver: str
    iftype: str
    ipv4_address: str
    ipv6_address: str
    lower_devs_list: List[Any]
    mtu: int
    nic_type: str
    operstate: str
    speed: int
    upper_devs_list: List[Any]


class HostFactsModel(BaseModel):
    arch: str
    bios_date: str
    bios_version: str
    cpu_cores: int
    cpu_count: int
    cpu_load: Dict[str, float]
    cpu_model: str
    cpu_threads: int
    flash_capacity: str
    flash_capacity_bytes: int
    flash_count: int
    flash_list: List[Any]
    hdd_capacity: str
    hdd_capacity_bytes: int
    hdd_count: int
    hdd_list: List[DeviceModel]
    hostname: str
    interfaces: Dict[str, NICModel]
    nic_count: int
    kernel: str
    kernel_parameters: Dict[str, Any]
    kernel_security: Dict[str, Any]
    memory_available_kb: int
    memory_free_kb: int
    memory_total_kb: int
    model: str
    operating_system: str
    subscribed: str
    system_uptime: float
    timestamp: float
    vendor: str


class DeviceSysInfoModel(BaseModel):
    human_readable_size: str
    locked: int
    model: str
    nr_requests: int
    partitions: Dict[str, Any]
    removable: bool
    rev: str
    ro: bool
    rotational: bool
    sas_address: str
    sas_device_handle: str
    scheduler_mode: str
    sectors: int
    sectorsize: int
    size: int
    support_discard: int
    vendor: str


class LogicalVolumeEntryModel(BaseModel):
    block_uuid: str
    cluster_fsid: str
    cluster_name: str
    name: str
    osd_fsid: str
    osd_id: int
    osdspec_affinity: str
    type: str


class VolumeDeviceModel(BaseModel):
    available: bool
    device_id: str
    human_readable_type: str = Field("")
    lsm_data: Dict[str, Any]
    lvs: List[LogicalVolumeEntryModel]
    path: str
    rejected_reasons: List[str]
    sys_api: DeviceSysInfoModel


class NodeCPULoadModel(BaseModel):
    one_min: float
    five_min: float
    fifteen_min: float


class NodeCPUInfoModel(BaseModel):
    arch: str
    model: str
    cores: int
    count: int
    threads: int
    load: NodeCPULoadModel


class NodeMemoryInfoModel(BaseModel):
    available_kb: int
    free_kb: int
    total_kb: int


class NodeInfoModel(BaseModel):
    hostname: str
    model: str
    vendor: str
    kernel: str
    operating_system: str
    system_uptime: float
    current_time: int
    cpu: NodeCPUInfoModel
    nics: Dict[str, NICModel]
    memory: NodeMemoryInfoModel
    disks: List[VolumeDeviceModel]
