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

# pyright: reportUnknownMemberType=false, reportMissingTypeStubs=false
# pyright: reportPrivateUsage=false

import os
from typing import Callable, List, Optional, Tuple

import pytest
from pyfakefs import fake_filesystem
from pytest_mock import MockerFixture

from gravel.controllers.gstate import GlobalState

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def test_get_mounts(fs: fake_filesystem.FakeFilesystem) -> None:

    fs.add_real_file(
        source_path=os.path.join(DATA_DIR, "mounts_with_aquarium.raw"),
        target_path="/proc/mounts",
    )

    from gravel.controllers.nodes.systemdisk import MountEntry, get_mounts

    lst: List[MountEntry] = get_mounts()
    found = False
    for entry in lst:
        if (
            entry.source == "/dev/mapper/aquarium-systemdisk"
            and entry.dest == "/var/lib/aquarium-system"
        ):
            found = True
            break
    assert found


def test_silly_mounts(fs: fake_filesystem.FakeFilesystem) -> None:
    fs.add_real_file(
        source_path=os.path.join(DATA_DIR, "mounts_silly.raw"),
        target_path="/proc/mounts",
    )

    from gravel.controllers.nodes.systemdisk import MountEntry, get_mounts

    lst: List[MountEntry] = get_mounts()
    assert len(lst) == 2
    assert lst[0].source == "foo" and lst[0].dest == "bar"
    assert lst[1].source == "asd" and lst[1].dest == "fgh"


def test_mounted(fs: fake_filesystem.FakeFilesystem) -> None:

    fs.add_real_file(
        source_path=os.path.join(DATA_DIR, "mounts_with_aquarium.raw"),
        target_path="/proc/mounts",
    )

    from gravel.controllers.nodes.systemdisk import SystemDisk

    systemdisk = SystemDisk()
    assert systemdisk.mounted


def test_not_mounted(fs: fake_filesystem.FakeFilesystem) -> None:

    fs.add_real_file(
        source_path=os.path.join(DATA_DIR, "mounts_without_aquarium.raw"),
        target_path="/proc/mounts",
    )

    from gravel.controllers.nodes.systemdisk import SystemDisk

    systemdisk = SystemDisk()
    assert not systemdisk.mounted


@pytest.mark.asyncio
async def test_lvm(mocker: MockerFixture) -> None:

    called_lvm_success = False
    called_lvm_failure = False

    async def mock_success_call(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        assert "lvm" in cmd
        nonlocal called_lvm_success
        called_lvm_success = True
        return 0, None, None

    async def mock_failure_call(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        assert "lvm" in cmd
        nonlocal called_lvm_failure
        called_lvm_failure = True
        return 1, None, "foobar"

    from gravel.controllers.nodes.systemdisk import LVMError, lvm

    mocker.patch(
        "gravel.controllers.nodes.systemdisk.aqr_run_cmd", new=mock_success_call
    )

    await lvm(["foo", "bar", "baz"])
    assert called_lvm_success

    mocker.patch(
        "gravel.controllers.nodes.systemdisk.aqr_run_cmd", new=mock_failure_call
    )
    try:
        await lvm(["foo", "bar", "baz"])
    except LVMError as e:
        assert e.message == "foobar"
    assert called_lvm_failure


# @pytest.mark.asyncio
async def _disable_test_create(
    gstate: GlobalState,
    fs: fake_filesystem.FakeFilesystem,
    mocker: MockerFixture,
    get_data_contents: Callable[[str, str], str],
) -> None:
    async def mock_call(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        return 0, None, None

    async def mock_lvm(args: str) -> None:
        if "lvcreate" in args:
            if "systemdisk" in args:
                fs.create_file("/dev/mapper/aquarium-systemdisk")
            elif "containers" in args:
                fs.create_file("/dev/mapper/aquarium-containers")

    from gravel.controllers.inventory.inventory import Inventory
    from gravel.controllers.inventory.nodeinfo import NodeInfoModel
    from gravel.controllers.nodes.systemdisk import (
        SystemDisk,
        UnavailableDeviceError,
        UnknownDeviceError,
    )

    nodeinfo: NodeInfoModel = NodeInfoModel.parse_raw(
        get_data_contents(DATA_DIR, "nodeinfo_real.json")
    )

    inventory: Inventory = gstate.inventory
    inventory.probe = mocker.AsyncMock()
    inventory._latest = nodeinfo

    systemdisk = SystemDisk()
    mocker.patch(
        "gravel.controllers.nodes.systemdisk.aqr_run_cmd", new=mock_call
    )
    mocker.patch("gravel.controllers.nodes.systemdisk.lvm", new=mock_lvm)
    throws = False
    try:
        await systemdisk.create("/dev/foobar")
    except UnknownDeviceError:
        throws = True
        pass
    assert throws

    nodeinfo.disks[0].available = False
    throws = False
    try:
        await systemdisk.create("/dev/vda")
    except UnavailableDeviceError:
        throws = True
        pass
    assert throws

    nodeinfo.disks[0].available = True
    await systemdisk.create("/dev/vda")


@pytest.mark.asyncio
async def test_mount_error(
    fs: fake_filesystem.FakeFilesystem,
    mocker: MockerFixture,
) -> None:
    async def mock_call(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        raise Exception("Failed mount.")

    mocker.patch(
        "gravel.controllers.nodes.systemdisk.aqr_run_cmd", new=mock_call
    )
    from gravel.controllers.nodes.systemdisk import MountError, SystemDisk

    systemdisk = SystemDisk()
    asserted = False
    try:
        await systemdisk.mount()
    except AssertionError:
        asserted = True
    assert asserted

    fs.create_file("/dev/mapper/aquarium-systemdisk")
    throws = False
    try:
        await systemdisk.mount()
    except MountError:
        throws = True
    assert throws
    assert fs.exists("/var/lib/aquarium-system")


@pytest.mark.asyncio
async def test_unmount_error(
    fs: fake_filesystem.FakeFilesystem,
    mocker: MockerFixture,
) -> None:
    async def mock_call(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        raise Exception("Failed unmount.")

    mocker.patch(
        "gravel.controllers.nodes.systemdisk.aqr_run_cmd", new=mock_call
    )
    from gravel.controllers.nodes.systemdisk import MountError, SystemDisk

    systemdisk = SystemDisk()
    throws = False
    try:
        await systemdisk.unmount()
    except MountError as e:
        assert "does not exist" in e.message
        throws = True
    assert throws

    fs.create_dir("/var/lib/aquarium-system")
    throws = False
    try:
        await systemdisk.unmount()
    except MountError as e:
        assert "failed unmount" in e.message.lower()
        throws = True
    assert throws


@pytest.mark.asyncio
async def test_enable(
    fs: fake_filesystem.FakeFilesystem,
    mocker: MockerFixture,
) -> None:

    from gravel.controllers.nodes.systemdisk import (
        MountError,
        OverlayError,
        SystemDisk,
    )

    async def mount_fail() -> None:
        raise MountError("Failed mount.")

    overlayed_paths = []
    bindmounts = []

    async def mock_call(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:

        if cmd[2] == "overlay":
            assert "lower" in cmd[4]
            lowerstr = (cmd[4].split(","))[0]
            lower = (lowerstr.split("="))[1]
            overlayed_paths.append(lower)
        elif cmd[1] == "--bind":
            assert len(cmd) == 4
            bindmounts.append(cmd[3])
        else:
            raise Exception(f"Unknown call: {cmd}")
        return 0, None, None

    # ensure we don't have a mounted fs
    fs.add_real_file(
        source_path=os.path.join(DATA_DIR, "mounts_without_aquarium.raw"),
        target_path="/proc/mounts",
    )

    systemdisk = SystemDisk()
    assert not systemdisk.mounted
    systemdisk.mount = mount_fail

    mocker.patch(
        "gravel.controllers.nodes.systemdisk.aqr_run_cmd", new=mock_call
    )

    throws = False
    try:
        await systemdisk.enable()
    except OverlayError as e:
        assert "failed mount" in e.message.lower()
        throws = True
    assert throws

    systemdisk.mount = mocker.AsyncMock()

    for upper in systemdisk._overlaydirs.keys():
        fs.create_dir(f"/var/lib/aquarium-system/{upper}/overlay")
        fs.create_dir(f"/var/lib/aquarium-system/{upper}/temp")

    for ours in systemdisk._bindmounts.keys():
        fs.create_dir(f"/var/lib/aquarium-system/{ours}")

    await systemdisk.enable()

    for lower in systemdisk._overlaydirs.values():
        assert fs.exists(lower)
        assert lower in overlayed_paths

    for theirs in systemdisk._bindmounts.values():
        assert fs.exists(theirs)
        assert theirs in bindmounts
