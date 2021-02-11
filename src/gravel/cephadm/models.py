# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from typing import Any, Dict, List
from pydantic import BaseModel


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
    timestamp: int
    vendor: str
