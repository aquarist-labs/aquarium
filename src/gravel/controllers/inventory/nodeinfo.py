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

from typing import Dict, List

from pydantic import BaseModel

from gravel.cephadm.cephadm import Cephadm, CephadmError
from gravel.cephadm.models import (
    NICModel,
    NodeCPUInfoModel,
    NodeCPULoadModel,
    NodeMemoryInfoModel,
    VolumeDeviceModel,
)


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


async def get_node_info(cephadm: Cephadm) -> NodeInfoModel:
    try:
        facts = await cephadm.gather_facts()
        inventory = await cephadm.get_volume_inventory()
    except CephadmError as e:
        raise CephadmError("error obtaining node info") from e

    return NodeInfoModel(
        hostname=facts.hostname,
        model=facts.model,
        vendor=facts.vendor,
        kernel=facts.kernel,
        operating_system=facts.operating_system,
        system_uptime=facts.system_uptime,
        current_time=facts.timestamp,
        cpu=NodeCPUInfoModel(
            arch=facts.arch,
            model=facts.cpu_model,
            cores=facts.cpu_cores,
            count=facts.cpu_count,
            threads=facts.cpu_threads,
            load=NodeCPULoadModel(
                one_min=facts.cpu_load["1min"],
                five_min=facts.cpu_load["5min"],
                fifteen_min=facts.cpu_load["15min"],
            ),
        ),
        nics=facts.interfaces,
        memory=NodeMemoryInfoModel(
            available_kb=facts.memory_available_kb,
            free_kb=facts.memory_free_kb,
            total_kb=facts.memory_total_kb,
        ),
        disks=inventory,
    )
