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

import pytest
from pytest_mock import MockerFixture

from gravel.controllers.nodes.local import (
    CPUQualifiedEnum,
    CPUQualifiedModel,
    LocalhostQualifiedModel,
    MemoryQualifiedEnum,
    MemoryQualifiedModel,
    RootDiskQualifiedEnum,
    RootDiskQualifiedModel,
    localhost_qualified,
    validate_cpu,
    validate_memory,
    validate_root_disk,
)


class FakeMemory:
    def __init__(self, total: int):
        self.total = total


class FakeDisk:
    def __init__(self, total: int):
        self.total = total


@pytest.mark.asyncio
async def test_validate_cpu(mocker: MockerFixture):
    # Check when we pass
    mocker.patch("psutil.cpu_count", return_value=8)
    results: CPUQualifiedModel = await validate_cpu()
    assert results.qualified is True
    assert results.min_cpu == 2
    assert results.actual_cpu == 8
    assert results.error == ""
    assert results.status == CPUQualifiedEnum.QUALIFIED

    # Check when we fail
    mocker.patch("psutil.cpu_count", return_value=1)
    results: CPUQualifiedModel = await validate_cpu()
    assert results.qualified is False
    assert results.min_cpu == 2
    assert results.actual_cpu == 1
    assert results.error == (
        "The node does not have a sufficient number of CPU cores. "
        "Required: 2, Actual: 1."
    )
    assert results.status == CPUQualifiedEnum.INSUFFICIENT_CORES


@pytest.mark.asyncio
async def test_validate_memory(mocker: MockerFixture):
    # Check when we pass
    mocker.patch(
        "psutil.virtual_memory", return_value=FakeMemory(total=33498816512)
    )
    results: MemoryQualifiedModel = await validate_memory()
    assert results.qualified is True
    assert results.min_mem == 2147483648
    assert results.actual_mem == 33498816512
    assert results.error == ""
    assert results.status == MemoryQualifiedEnum.QUALIFIED

    # Check when we fail
    mocker.patch(
        "psutil.virtual_memory", return_value=FakeMemory(total=1073741824)
    )
    results: MemoryQualifiedModel = await validate_memory()
    assert results.qualified is False
    assert results.min_mem == 2147483648
    assert results.actual_mem == 1073741824
    assert results.error == (
        "The node does not have a sufficient memory. Required: 2GB, Actual: 1GB."
    )
    assert results.status == MemoryQualifiedEnum.INSUFFICIENT_MEMORY


@pytest.mark.asyncio
async def test_validate_root_disk(mocker: MockerFixture):
    # Check when we pass
    mocker.patch("psutil.disk_usage", return_value=FakeDisk(total=20000000000))
    results: RootDiskQualifiedModel = await validate_root_disk()
    assert results.qualified is True
    assert results.min_disk == 10737418240
    assert results.actual_disk == 20000000000
    assert results.error == ""
    assert results.status == RootDiskQualifiedEnum.QUALIFIED

    # Check when we fail
    mocker.patch("psutil.disk_usage", return_value=FakeDisk(total=1073741824))
    results: RootDiskQualifiedModel = await validate_root_disk()
    assert results.qualified is False
    assert results.min_disk == 10737418240
    assert results.actual_disk == 1073741824
    assert results.error == (
        "The node does not have sufficient space on the root disk. "
        "Required: 10GB, Actual: 1GB."
    )
    assert results.status == RootDiskQualifiedEnum.INSUFFICIENT_SPACE


@pytest.mark.asyncio
async def test_localhost_qualified(mocker: MockerFixture):
    # Check when we pass
    mocker.patch("psutil.cpu_count", return_value=8)
    mocker.patch(
        "psutil.virtual_memory", return_value=FakeMemory(total=33498816512)
    )
    mocker.patch("psutil.disk_usage", return_value=FakeDisk(total=20000000000))
    results: LocalhostQualifiedModel = await localhost_qualified()
    assert results.all_qualified is True
    assert results.cpu_qualified.qualified is True
    assert results.cpu_qualified.min_cpu == 2
    assert results.cpu_qualified.actual_cpu == 8
    assert results.cpu_qualified.error == ""
    assert results.cpu_qualified.status == CPUQualifiedEnum.QUALIFIED
    assert results.mem_qualified.qualified is True
    assert results.mem_qualified.min_mem == 2147483648
    assert results.mem_qualified.actual_mem == 33498816512
    assert results.mem_qualified.error == ""
    assert results.mem_qualified.status == MemoryQualifiedEnum.QUALIFIED
    assert results.root_disk_qualified.qualified is True
    assert results.root_disk_qualified.min_disk == 10737418240
    assert results.root_disk_qualified.actual_disk == 20000000000
    assert results.root_disk_qualified.error == ""
    assert results.root_disk_qualified.status == RootDiskQualifiedEnum.QUALIFIED

    # Check when we fail just CPU
    mocker.patch("psutil.cpu_count", return_value=1)
    results: LocalhostQualifiedModel = await localhost_qualified()
    assert results.all_qualified is False
    assert results.cpu_qualified.qualified is False
    assert results.cpu_qualified.min_cpu == 2
    assert results.cpu_qualified.actual_cpu == 1
    assert results.cpu_qualified.error == (
        "The node does not have a sufficient number of CPU cores. "
        "Required: 2, Actual: 1."
    )
    assert results.cpu_qualified.status == CPUQualifiedEnum.INSUFFICIENT_CORES
    assert results.mem_qualified.qualified is True
    assert results.mem_qualified.min_mem == 2147483648
    assert results.mem_qualified.actual_mem == 33498816512
    assert results.mem_qualified.error == ""
    assert results.mem_qualified.status == MemoryQualifiedEnum.QUALIFIED
    assert results.root_disk_qualified.qualified is True
    assert results.root_disk_qualified.min_disk == 10737418240
    assert results.root_disk_qualified.actual_disk == 20000000000
    assert results.root_disk_qualified.error == ""
    assert results.root_disk_qualified.status == RootDiskQualifiedEnum.QUALIFIED

    # Check when we fail CPU + Disk
    mocker.patch("psutil.cpu_count", return_value=1)
    mocker.patch("psutil.disk_usage", return_value=FakeDisk(total=1073741824))
    results: LocalhostQualifiedModel = await localhost_qualified()
    assert results.cpu_qualified.qualified is False
    assert results.cpu_qualified.min_cpu == 2
    assert results.cpu_qualified.actual_cpu == 1
    assert results.cpu_qualified.error == (
        "The node does not have a sufficient number of CPU cores. "
        "Required: 2, Actual: 1."
    )
    assert results.cpu_qualified.status == CPUQualifiedEnum.INSUFFICIENT_CORES
    assert results.mem_qualified.qualified is True
    assert results.mem_qualified.min_mem == 2147483648
    assert results.mem_qualified.actual_mem == 33498816512
    assert results.mem_qualified.error == ""
    assert results.mem_qualified.status == MemoryQualifiedEnum.QUALIFIED
    assert results.root_disk_qualified.qualified is False
    assert results.root_disk_qualified.min_disk == 10737418240
    assert results.root_disk_qualified.actual_disk == 1073741824
    assert results.root_disk_qualified.error == (
        "The node does not have sufficient space on the root disk. "
        "Required: 10GB, Actual: 1GB."
    )
    assert (
        results.root_disk_qualified.status
        == RootDiskQualifiedEnum.INSUFFICIENT_SPACE
    )
