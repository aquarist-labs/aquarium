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

import psutil
from pydantic import BaseModel, Field

# Minimum requirements for individual host validation:
# NOTE(jhesketh): These are obviously hardcoded for the moment, but may be
#                 better moved into some kind of support matrix (eg feature
#                 vs hardware etc).
#                 These are also currently somewhat arbitrary and will need
#                 tuning.
AQUARIUM_MIN_CPU = 2
AQUARIUM_MIN_MEMORY_GB = 2
AQUARIUM_MIN_ROOT_DISK_GB = 10


class CPUQualifiedEnum(int, Enum):
    QUALIFIED = 0
    INSUFFICIENT_CORES = 1


class CPUQualifiedModel(BaseModel):
    qualified: bool = Field("The CPU is sufficient")
    min_cpu: int = Field("Minimum number of CPU's")
    actual_cpu: int = Field("Actual number of CPU's")
    error: str = Field("CPU didn't meet requirements")
    status: CPUQualifiedEnum = Field(CPUQualifiedEnum.QUALIFIED)


class MemoryQualifiedEnum(int, Enum):
    QUALIFIED = 0
    INSUFFICIENT_MEMORY = 1


class MemoryQualifiedModel(BaseModel):
    qualified: bool = Field("The memory is sufficient")
    min_mem: int = Field("Minimum amount of memory (GB)")
    actual_mem: int = Field("Actual amount of memory (GB)")
    error: str = Field("Memory didn't meet requirements")
    status: MemoryQualifiedEnum = Field(MemoryQualifiedEnum.QUALIFIED)


class RootDiskQualifiedEnum(int, Enum):
    QUALIFIED = 0
    INSUFFICIENT_SPACE = 1


class RootDiskQualifiedModel(BaseModel):
    qualified: bool = Field("The root disk size is sufficient")
    min_disk: int = Field("Minimum size of root disk (GB)")
    actual_disk: int = Field("Actual size of root disk (GB)")
    error: str = Field("Root disk didn't meet requirements")
    status: RootDiskQualifiedEnum = Field(RootDiskQualifiedEnum.QUALIFIED)


class LocalhostQualifiedModel(BaseModel):
    all_qualified: bool = Field("The localhost passes validation")
    cpu_qualified: CPUQualifiedModel = Field("CPU qualification details")
    mem_qualified: MemoryQualifiedModel = Field("Memory qualification details")
    root_disk_qualified: RootDiskQualifiedModel = Field(
        "Root disk qualification details"
    )


async def validate_cpu() -> CPUQualifiedModel:
    """
    Validates the localhost meets the minium CPU requirements.
    """
    qualified: bool = True
    min_cpu: int = AQUARIUM_MIN_CPU
    actual_cpu: int = psutil.cpu_count()
    error: str = ""
    status: CPUQualifiedEnum = CPUQualifiedEnum.QUALIFIED

    if actual_cpu < min_cpu:
        qualified = False
        error = (
            "The node does not have a sufficient number of CPU cores. "
            "Required: %d, Actual: %d." % (min_cpu, actual_cpu)
        )
        status = CPUQualifiedEnum.INSUFFICIENT_CORES

    return CPUQualifiedModel(
        qualified=qualified,
        min_cpu=min_cpu,
        actual_cpu=actual_cpu,
        error=error,
        status=status,
    )


async def validate_memory() -> MemoryQualifiedModel:
    """
    Validates the localhost meets the minium memory requirements.
    """
    qualified: bool = True
    min_mem: int = AQUARIUM_MIN_MEMORY_GB
    # 1024 kb / 1024 mb / 1024 gb
    # NOTE(jhesketh): We round down to the nearest GB
    actual_mem: int = int(psutil.virtual_memory().total / 1024 / 1024 / 1024)
    error: str = ""
    status: MemoryQualifiedEnum = MemoryQualifiedEnum.QUALIFIED

    if actual_mem < min_mem:
        qualified = False
        error = (
            "The node does not have a sufficient memory. "
            "Required: %d, Actual: %d." % (min_mem, actual_mem)
        )
        status = MemoryQualifiedEnum.INSUFFICIENT_MEMORY
    return MemoryQualifiedModel(
        qualified=qualified,
        min_mem=min_mem,
        actual_mem=actual_mem,
        error=error,
        status=status,
    )


async def validate_root_disk() -> RootDiskQualifiedModel:
    """
    Validates the localhost meets the minium disk requirements.

    NOTE: This only verifies the total size of the root partition. It does
          not validate the amount of free space etc.
    """
    qualified: bool = True
    min_disk: int = AQUARIUM_MIN_ROOT_DISK_GB
    # 1024 kb / 1024 mb / 1024 gb
    # NOTE(jhesketh): We round down to the nearest GB
    actual_disk: int = int(psutil.disk_usage("/").total / 1024 / 1024 / 1024)
    error: str = ""
    status: RootDiskQualifiedEnum = RootDiskQualifiedEnum.QUALIFIED

    if actual_disk < min_disk:
        qualified = False
        error = (
            "The node does not have sufficient space on the root disk. "
            "Required: %d, Actual: %d." % (min_disk, actual_disk)
        )
        status = RootDiskQualifiedEnum.INSUFFICIENT_SPACE
    return RootDiskQualifiedModel(
        qualified=qualified,
        min_disk=min_disk,
        actual_disk=actual_disk,
        error=error,
        status=status,
    )


async def localhost_qualified() -> LocalhostQualifiedModel:
    """
    Validates whether the localhost is fully qualified (ie, meets all minium
    requirements).
    """
    all_qualified: bool = True

    cputask = asyncio.create_task(validate_cpu())
    memtask = asyncio.create_task(validate_memory())
    disktask = asyncio.create_task(validate_root_disk())

    cpu_qualified: CPUQualifiedModel = await cputask
    mem_qualified: MemoryQualifiedModel = await memtask
    root_disk_qualified: RootDiskQualifiedModel = await disktask
    if not (
        cpu_qualified.qualified
        and mem_qualified.qualified
        and root_disk_qualified.qualified
    ):
        all_qualified = False

    result = LocalhostQualifiedModel(
        all_qualified=all_qualified,
        cpu_qualified=cpu_qualified,
        mem_qualified=mem_qualified,
        root_disk_qualified=root_disk_qualified,
    )
    return result
