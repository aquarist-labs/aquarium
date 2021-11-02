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

# pyright: reportPrivateUsage=false

import os
from typing import Callable

import pytest
from pytest_mock import MockerFixture

from gravel.controllers.gstate import GlobalState
from gravel.controllers.nodes.requirements import (
    CPUQualifiedEnum,
    CPUQualifiedModel,
    DisksQualifiedErrorEnum,
    MemoryQualifiedEnum,
    MemoryQualifiedModel,
    RequirementsModel,
    localhost_qualified,
    validate_cpu,
    validate_memory,
)


class FakeMemory:
    def __init__(self, total: int):
        self.total = total


class FakeDisk:
    def __init__(self, total: int):
        self.total = total


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.mark.asyncio
async def test_validate_cpu(mocker: MockerFixture):
    # Check when we pass
    mocker.patch("psutil.cpu_count", return_value=8)
    results: CPUQualifiedModel = await validate_cpu()
    assert results.qualified is True
    assert results.min_threads == 2
    assert results.actual_threads == 8
    assert results.error == ""
    assert results.status == CPUQualifiedEnum.QUALIFIED

    # Check when we fail
    mocker.patch("psutil.cpu_count", return_value=1)
    results: CPUQualifiedModel = await validate_cpu()
    assert results.qualified is False
    assert results.min_threads == 2
    assert results.actual_threads == 1
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
async def test_localhost_qualified(
    mocker: MockerFixture,
    gstate: GlobalState,
    get_data_contents: Callable[[str, str], str],
):
    # Check when we pass

    from gravel.controllers.inventory.nodeinfo import NodeInfoModel
    from gravel.controllers.nodes.disks import Disks, DiskSolution

    fake_inventory: NodeInfoModel = NodeInfoModel.parse_raw(
        get_data_contents(DATA_DIR, "disks_local_nodeinfo.json")
    )
    gstate.inventory._latest = fake_inventory

    mocker.patch("psutil.cpu_count", return_value=8)
    mocker.patch(
        "psutil.virtual_memory", return_value=FakeMemory(total=33498816512)
    )
    results: RequirementsModel = await localhost_qualified(gstate)
    assert results.qualified is True
    assert results.cpu.qualified is True
    assert results.cpu.min_threads == 2
    assert results.cpu.actual_threads == 8
    assert results.cpu.error == ""
    assert results.cpu.status == CPUQualifiedEnum.QUALIFIED
    assert results.mem.qualified is True
    assert results.mem.min_mem == 2147483648
    assert results.mem.actual_mem == 33498816512
    assert results.mem.error == ""
    assert results.mem.status == MemoryQualifiedEnum.QUALIFIED
    assert results.disks.available.qualified
    assert results.disks.available.status == DisksQualifiedErrorEnum.NONE
    assert results.disks.available.min == 1
    assert results.disks.available.actual == 4
    assert results.disks.install.qualified
    assert results.disks.install.status == DisksQualifiedErrorEnum.NONE
    assert results.disks.install.min == 10737418240
    assert results.disks.install.actual == 10737418240

    # Check when we fail just CPU
    mocker.patch("psutil.cpu_count", return_value=1)
    results = await localhost_qualified(gstate)
    assert results.qualified is False
    assert results.cpu.qualified is False
    assert results.cpu.min_threads == 2
    assert results.cpu.actual_threads == 1
    assert results.cpu.error == (
        "The node does not have a sufficient number of CPU cores. "
        "Required: 2, Actual: 1."
    )
    assert results.cpu.status == CPUQualifiedEnum.INSUFFICIENT_CORES
    assert results.mem.qualified is True
    assert results.mem.min_mem == 2147483648
    assert results.mem.actual_mem == 33498816512
    assert results.mem.error == ""
    assert results.mem.status == MemoryQualifiedEnum.QUALIFIED
