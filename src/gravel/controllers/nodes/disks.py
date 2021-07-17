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

from enum import Enum
from logging import Logger
from typing import List, Optional, Tuple
from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field

from gravel.cephadm.models import NodeInfoModel, VolumeDeviceModel
from gravel.controllers.gstate import GlobalState


logger: Logger = fastapi_logger


class DiskTypeEnum(int, Enum):
    NONE = 0
    HDD = 1
    SSD = 2


class DiskInfoModel(BaseModel):
    vendor: str = Field("", title="disk's manufacturer")
    model: str = Field("", title="disk's model")


class DiskModel(BaseModel):
    path: Optional[str] = Field(None, title="disk's device path")
    size: int = Field(0, title="size in bytes")
    type: DiskTypeEnum = Field(DiskTypeEnum.NONE, title="disk type")
    info: DiskInfoModel = Field(
        DiskInfoModel(), title="additional info about disk"
    )


class RejectedDiskModel(BaseModel):
    disk: DiskModel = Field(title="rejected disk")
    reasons: List[str] = Field([], title="reasons for rejection")


class DiskSolution(BaseModel):
    systemdisk: Optional[DiskModel] = Field(None, title="chosen system disk")
    storage: List[DiskModel] = Field([], title="chosen storage disks")
    storage_size: int = Field(0, title="total size for storage, in bytes")
    rejected: List[RejectedDiskModel] = Field([], title="rejected disks")
    possible: bool = Field(False, title="deployment possible")


def _device_to_disk(device: VolumeDeviceModel) -> DiskModel:
    def _get_disk_type(rotational: bool) -> DiskTypeEnum:
        return DiskTypeEnum.HDD if rotational else DiskTypeEnum.SSD

    return DiskModel(
        path=device.path,
        size=device.sys_api.size,
        type=_get_disk_type(device.sys_api.rotational),
        info=DiskInfoModel(
            vendor=device.sys_api.vendor, model=device.sys_api.model
        ),
    )


class Disks:
    def __init__(self) -> None:
        pass

    @classmethod
    def gen_solution(cls, gstate: GlobalState) -> DiskSolution:

        nodeinfo: Optional[NodeInfoModel] = gstate.inventory.latest
        assert nodeinfo

        hdds: List[VolumeDeviceModel] = []
        ssds: List[VolumeDeviceModel] = []
        rejected: List[VolumeDeviceModel] = []

        for device in nodeinfo.disks:
            if not device.available:
                rejected.append(device)
                continue

            if device.sys_api.rotational:
                hdds.append(device)
            else:
                ssds.append(device)

        def _get_candidates(
            lst: List[VolumeDeviceModel],
        ) -> Tuple[Optional[VolumeDeviceModel], List[VolumeDeviceModel]]:
            systemdisk: Optional[VolumeDeviceModel] = None
            storage: List[VolumeDeviceModel] = []
            for entry in lst:
                if not systemdisk:
                    systemdisk = entry
                elif systemdisk.sys_api.size > entry.sys_api.size:
                    storage.append(systemdisk)
                    systemdisk = entry
                else:
                    storage.append(entry)
            return systemdisk, storage

        candidate_storage: List[VolumeDeviceModel] = []
        candidate_systemdisk: Optional[VolumeDeviceModel] = None
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

        for device in rejected:
            solution.rejected.append(
                RejectedDiskModel(
                    disk=_device_to_disk(device),
                    reasons=device.rejected_reasons,
                )
            )

        if not candidate_systemdisk:
            return solution

        solution.systemdisk = _device_to_disk(candidate_systemdisk)
        total_storage = 0
        for device in candidate_storage:
            solution.storage.append(_device_to_disk(device))
            total_storage += device.sys_api.size
        solution.storage_size = total_storage

        return solution
