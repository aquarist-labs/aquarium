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
from typing import List, Optional, Tuple

from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field

from gravel.controllers.gstate import GlobalState
from gravel.controllers.inventory.disks import DiskDevice
from gravel.controllers.inventory.nodeinfo import NodeInfoModel

logger: Logger = fastapi_logger


class DiskSolution(BaseModel):
    systemdisk: Optional[DiskDevice] = Field(None, title="chosen system disk")
    storage: List[DiskDevice] = Field([], title="chosen storage disks")
    storage_size: int = Field(0, title="total size for storage, in bytes")
    rejected: List[DiskDevice] = Field([], title="rejected disks")
    possible: bool = Field(False, title="deployment possible")


class Disks:
    def __init__(self) -> None:
        pass

    @classmethod
    def gen_solution(cls, gstate: GlobalState) -> DiskSolution:

        nodeinfo: Optional[NodeInfoModel] = gstate.inventory.latest
        assert nodeinfo

        hdds: List[DiskDevice] = []
        ssds: List[DiskDevice] = []
        rejected: List[DiskDevice] = []

        for device in nodeinfo.disks:
            if not device.available:
                rejected.append(device)
                continue

            if device.rotational:
                hdds.append(device)
            else:
                ssds.append(device)

        def _get_candidates(
            lst: List[DiskDevice],
        ) -> Tuple[Optional[DiskDevice], List[DiskDevice]]:
            systemdisk: Optional[DiskDevice] = None
            storage: List[DiskDevice] = []
            for entry in lst:
                if not systemdisk:
                    systemdisk = entry
                elif systemdisk.size > entry.size:
                    storage.append(systemdisk)
                    systemdisk = entry
                else:
                    storage.append(entry)
            return systemdisk, storage

        candidate_storage: List[DiskDevice] = []
        candidate_systemdisk: Optional[DiskDevice] = None
        candidate_systemdisk_hdd, hdd_lst = _get_candidates(hdds)
        candidate_systemdisk_ssd, ssd_lst = _get_candidates(ssds)

        candidate_storage = hdd_lst + ssd_lst

        if candidate_systemdisk_ssd:
            candidate_systemdisk = candidate_systemdisk_ssd
            if candidate_systemdisk_hdd:
                candidate_storage.append(candidate_systemdisk_hdd)
        elif candidate_systemdisk_hdd:
            candidate_systemdisk = candidate_systemdisk_hdd

        if len(hdds) + len(ssds) > 0:
            assert candidate_systemdisk
            assert len(candidate_storage) + 1 == len(hdds) + len(ssds)

        solution = DiskSolution()
        solution.possible = candidate_systemdisk is not None
        solution.rejected = rejected

        if not candidate_systemdisk:
            return solution

        solution.systemdisk = candidate_systemdisk
        solution.storage = candidate_storage
        total_storage = 0
        for device in candidate_storage:
            total_storage += device.size
        solution.storage_size = total_storage

        return solution
