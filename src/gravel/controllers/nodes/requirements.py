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

import asyncio
from enum import Enum
from typing import List

import psutil
from pydantic import BaseModel, Field

from gravel.controllers.gstate import GlobalState
from gravel.controllers.inventory.disks import DiskDevice, get_storage_devices

# Minimum requirements for individual host validation:
# NOTE(jhesketh): These are obviously hardcoded for the moment, but may be
#                 better moved into some kind of support matrix (eg feature
#                 vs hardware etc).
#                 These are also currently somewhat arbitrary and will need
#                 tuning.
AQUARIUM_MIN_CPU_THREADS = 2
AQUARIUM_MIN_MEMORY = 2 * 1024 * 1024 * 1024  # 2 * KB * MB * GB
AQUARIUM_MIN_SYSTEM_DISK = 10 * 1024 * 1024 * 1024  # 2 * KB * MB * GB
AQUARIUM_MIN_AVAIL_DISKS = 1


class CPUQualifiedEnum(int, Enum):
    QUALIFIED = 0
    INSUFFICIENT_CORES = 1


class CPUQualifiedModel(BaseModel):
    qualified: bool = Field("The CPU is sufficient")
    min_threads: int = Field("Minimum number of CPU threads")
    actual_threads: int = Field("Actual number of CPU threads")
    error: str = Field("CPU didn't meet requirements")
    status: CPUQualifiedEnum = Field(CPUQualifiedEnum.QUALIFIED)


class MemoryQualifiedEnum(int, Enum):
    QUALIFIED = 0
    INSUFFICIENT_MEMORY = 1


class MemoryQualifiedModel(BaseModel):
    qualified: bool = Field("The memory is sufficient")
    min_mem: int = Field("Minimum amount of memory (bytes)")
    actual_mem: int = Field("Actual amount of memory (bytes)")
    error: str = Field("Memory didn't meet requirements")
    status: MemoryQualifiedEnum = Field(MemoryQualifiedEnum.QUALIFIED)


class DisksQualifiedErrorEnum(int, Enum):
    NONE = 0
    INSUFFICIENT_DISKS = 1
    INSUFFICENT_SPACE = 2


class DisksQualifiedStatusModel(BaseModel):
    qualified: bool = Field("Resource meets requirements.")
    min: int = Field(title="Minimum of resource.")
    actual: int = Field(title="Actual quantity of resource.")
    error: str = Field(title="Error message.")
    status: DisksQualifiedErrorEnum = Field(title="Error status code.")


class DisksQualifiedModel(BaseModel):
    available: DisksQualifiedStatusModel = Field("Host's available disks.")
    install: DisksQualifiedStatusModel = Field("Host's install disk.")

    @property
    def qualified(self) -> bool:
        return self.available.qualified and self.install.qualified


class RequirementsModel(BaseModel):
    qualified: bool = Field(title="The localhost passes validation.")
    impossible: bool = Field(title="Installation is impossible.")
    cpu: CPUQualifiedModel = Field(title="CPU qualification details.")
    mem: MemoryQualifiedModel = Field(title="Memory qualification details.")
    disks: DisksQualifiedModel = Field(title="Disk qualification details.")


async def validate_cpu() -> CPUQualifiedModel:
    """
    Validates the localhost meets the minium CPU requirements.
    """
    qualified: bool = True
    min_threads: int = AQUARIUM_MIN_CPU_THREADS
    actual_threads: int = psutil.cpu_count()
    error: str = ""
    status: CPUQualifiedEnum = CPUQualifiedEnum.QUALIFIED

    if actual_threads < min_threads:
        qualified = False
        error = (
            "The node does not have a sufficient number of CPU cores. "
            "Required: %d, Actual: %d." % (min_threads, actual_threads)
        )
        status = CPUQualifiedEnum.INSUFFICIENT_CORES

    return CPUQualifiedModel(
        qualified=qualified,
        min_threads=min_threads,
        actual_threads=actual_threads,
        error=error,
        status=status,
    )


async def validate_memory() -> MemoryQualifiedModel:
    """
    Validates the localhost meets the minium memory requirements.
    """
    qualified: bool = True
    min_mem: int = AQUARIUM_MIN_MEMORY
    actual_mem: int = psutil.virtual_memory().total
    error: str = ""
    status: MemoryQualifiedEnum = MemoryQualifiedEnum.QUALIFIED

    if actual_mem < min_mem:
        qualified = False
        # 1024 kb / 1024 mb / 1024 gb
        # NOTE(jhesketh): We round down to the nearest GB
        min_mem_gb: int = int(min_mem / 1024 / 1024 / 1024)
        actual_mem_gb: int = int(actual_mem / 1024 / 1024 / 1024)
        error = (
            "The node does not have a sufficient memory. "
            "Required: %dGB, Actual: %dGB." % (min_mem_gb, actual_mem_gb)
        )
        status = MemoryQualifiedEnum.INSUFFICIENT_MEMORY
    return MemoryQualifiedModel(
        qualified=qualified,
        min_mem=min_mem,
        actual_mem=actual_mem,
        error=error,
        status=status,
    )


async def validate_disks() -> DisksQualifiedModel:
    devices: List[DiskDevice] = await get_storage_devices()

    avail: List[DiskDevice] = [d for d in devices if d.available]
    avail_min = AQUARIUM_MIN_AVAIL_DISKS
    avail_actual = len(avail)
    avail_status = DisksQualifiedErrorEnum.NONE
    avail_error = ""
    avail_qualified = avail_actual >= avail_min

    if not avail_qualified:
        avail_status = DisksQualifiedErrorEnum.INSUFFICIENT_DISKS
        avail_error = "The node doesn't have enough disks available."

    install_min = AQUARIUM_MIN_SYSTEM_DISK
    install_actual = 0
    install_status = DisksQualifiedErrorEnum.NONE
    install_error = ""

    candidates: List[DiskDevice] = []
    for disk in avail:
        if disk.size >= install_min:
            candidates.append(disk)
        install_actual = max(disk.size, install_actual)

    install_qualified = len(candidates) > 0
    if not install_qualified:
        install_status = DisksQualifiedErrorEnum.INSUFFICENT_SPACE
        install_error = (
            "The node doesn't have an available disk with sufficient "
            "space for installation."
        )

    return DisksQualifiedModel(
        available=DisksQualifiedStatusModel(
            qualified=avail_qualified,
            min=avail_min,
            actual=avail_actual,
            error=avail_error,
            status=avail_status,
        ),
        install=DisksQualifiedStatusModel(
            qualified=install_qualified,
            min=install_min,
            actual=install_actual,
            error=install_error,
            status=install_status,
        ),
    )


async def localhost_qualified() -> RequirementsModel:
    """
    Validates whether the localhost is fully qualified (ie, meets all minium
    requirements).
    """
    all_qualified: bool = True

    cpu_qualified: CPUQualifiedModel
    mem_qualified: MemoryQualifiedModel
    disks_qualified: DisksQualifiedModel
    cpu_qualified, mem_qualified, disks_qualified = await asyncio.gather(
        validate_cpu(), validate_memory(), validate_disks()
    )

    if not (
        cpu_qualified.qualified
        and mem_qualified.qualified
        and disks_qualified.qualified
    ):
        all_qualified = False

    # if we don't qualify for disks, then it's impossible to install.
    impossible = not disks_qualified.qualified

    result = RequirementsModel(
        qualified=all_qualified,
        impossible=impossible,
        cpu=cpu_qualified,
        mem=mem_qualified,
        disks=disks_qualified,
    )
    return result
