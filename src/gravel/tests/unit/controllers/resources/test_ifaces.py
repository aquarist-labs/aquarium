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

# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
# pyright: reportMissingTypeStubs=false

import os
from typing import Any, Callable, Dict, List, Optional, Tuple
import pytest
from pyfakefs import fake_filesystem
from pytest_mock import MockerFixture


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.mark.asyncio
async def test_interfaces(
    mocker: MockerFixture,
    get_data_contents: Callable[[str, str], str],
    fs: fake_filesystem.FakeFilesystem,
) -> None:

    from gravel.controllers.resources.ifaces import (
        Interfaces,
        UnknownInterfaceError,
    )

    async def mock_call(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        assert "lshw" in cmd
        out = get_data_contents(DATA_DIR, "lshw.json")
        return 0, out, None

    interfaces = Interfaces(1.0)
    interfaces._update_statistics = mocker.MagicMock()
    mocker.patch(
        "gravel.controllers.resources.ifaces.aqr_run_cmd", new=mock_call
    )
    fs.add_real_file(
        source_path=os.path.join(DATA_DIR, "ifcfg-eno1"),
        target_path="/etc/sysconfig/network/ifcfg-eno1",
    )
    fs.add_real_file(
        source_path=os.path.join(DATA_DIR, "ifcfg-enp34s0"),
        target_path="/etc/sysconfig/network/ifcfg-enp34s0",
    )

    assert await interfaces._should_tick()

    await interfaces._do_tick()

    cards = interfaces.cards
    assert len(cards) > 0
    assert "0:21" in cards
    assert "0:22" in cards
    assert len(cards["0:21"].ports) == 1
    assert len(cards["0:22"].ports) == 1
    assert cards["0:21"].ports[0].name == "eno1"
    assert cards["0:22"].ports[0].name == "enp34s0"

    ifaces = interfaces.interfaces
    assert len(ifaces) > 0
    assert "enp34s0" in ifaces
    assert "eno1" in ifaces
    assert ifaces["enp34s0"].name == "enp34s0"
    assert ifaces["eno1"].name == "eno1"

    enp34s0 = ifaces["enp34s0"]
    eno1 = ifaces["eno1"]

    assert enp34s0.link
    assert enp34s0.config.bootproto == "static"
    assert enp34s0.config.address == "172.20.20.5"
    assert enp34s0.config.prefixlen == 24
    assert enp34s0.address == "172.20.20.5"

    assert not eno1.link
    assert eno1.config.bootproto == "dhcp"
    assert not eno1.config.address
    assert not eno1.config.prefixlen

    assert interfaces.get_interface("eno1") == eno1
    assert interfaces.get_interface("enp34s0") == enp34s0

    throws = False
    try:
        interfaces.get_interface("foobar")
    except UnknownInterfaceError as e:
        assert e.message == "foobar"
        throws = True
    assert throws


@pytest.mark.asyncio
async def test_raw_devices(mocker: MockerFixture) -> None:

    from gravel.controllers.resources.ifaces import (
        Interfaces,
        HardwareListError,
    )

    async def fail_call_one(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        return 1, None, "foobar"

    async def fail_call_two(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        return 0, None, None

    interfaces = Interfaces(1.0)

    mocker.patch(
        "gravel.controllers.resources.ifaces.aqr_run_cmd", new=fail_call_one
    )
    throws = False
    try:
        await interfaces._get_raw_devices()
    except HardwareListError as e:
        assert "foobar" in e.message
        throws = True
    assert throws

    mocker.patch(
        "gravel.controllers.resources.ifaces.aqr_run_cmd", new=fail_call_two
    )
    throws = False
    try:
        await interfaces._get_raw_devices()
    except HardwareListError as e:
        assert "no return" in e.message
        throws = True
    assert throws


@pytest.mark.asyncio
async def test_statistics(
    mocker: MockerFixture,
    get_data_contents: Callable[[str, str], str],
    fs: fake_filesystem.FakeFilesystem,
) -> None:

    from gravel.controllers.resources.ifaces import (
        Interfaces,
        UnknownInterfaceError,
    )

    class FakeCounter:
        bytes_recv: int
        bytes_sent: int

        def __init__(self, tx: int, rx: int) -> None:
            self.bytes_sent = tx
            self.bytes_recv = rx

    def counter_gen():
        yield {
            "eno1": FakeCounter(1000, 500),
            "enp34s0": FakeCounter(2000, 1000),
        }
        yield {
            "eno1": FakeCounter(1500, 700),
            "enp34s0": FakeCounter(3000, 2000),
        }

    def timestamp_gen():
        yield 50  # first call
        yield 50  # first call
        yield 51  # second call
        yield 51  # second call

    cntgen = counter_gen()
    tsgen = timestamp_gen()

    def mock_io_counters(pernic: bool, nowrap: bool) -> Dict[str, Any]:
        assert pernic
        assert nowrap
        return next(cntgen)

    def mock_timestamp() -> int:
        return next(tsgen)

    mocker.patch("psutil.net_io_counters", new=mock_io_counters)

    async def mock_lshw(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        assert "lshw" in cmd
        out = get_data_contents(DATA_DIR, "lshw.json")
        return 0, out, None

    mocker.patch(
        "gravel.controllers.resources.ifaces.aqr_run_cmd", new=mock_lshw
    )
    fs.add_real_file(
        source_path=os.path.join(DATA_DIR, "ifcfg-eno1"),
        target_path="/etc/sysconfig/network/ifcfg-eno1",
    )
    fs.add_real_file(
        source_path=os.path.join(DATA_DIR, "ifcfg-enp34s0"),
        target_path="/etc/sysconfig/network/ifcfg-enp34s0",
    )

    interfaces = Interfaces(1.0)
    interfaces._get_timestamp = mock_timestamp

    await interfaces._update_network_cards()

    interfaces._update_statistics()

    assert len(interfaces._statistics_by_name) == 0
    assert len(interfaces._last_statistics) == 2
    assert "eno1" in interfaces._last_statistics
    assert "enp34s0" in interfaces._last_statistics
    assert interfaces._last_statistics["eno1"].ts == 50
    assert interfaces._last_statistics["eno1"].tx == 1000
    assert interfaces._last_statistics["eno1"].rx == 500
    assert interfaces._last_statistics["enp34s0"].ts == 50
    assert interfaces._last_statistics["enp34s0"].tx == 2000
    assert interfaces._last_statistics["enp34s0"].rx == 1000

    interfaces._update_statistics()
    assert interfaces._last_statistics["eno1"].ts == 51
    assert interfaces._last_statistics["eno1"].tx == 1500
    assert interfaces._last_statistics["eno1"].rx == 700
    assert interfaces._last_statistics["enp34s0"].ts == 51
    assert interfaces._last_statistics["enp34s0"].tx == 3000
    assert interfaces._last_statistics["enp34s0"].rx == 2000

    stats = interfaces.stats
    assert "eno1" in stats
    assert "enp34s0" in stats
    assert len(stats["eno1"]) == 1
    assert len(stats["enp34s0"]) == 1
    assert stats["eno1"][0].tx == 500
    assert stats["eno1"][0].rx == 200
    assert stats["eno1"][0].ts == 51
    assert stats["enp34s0"][0].tx == 1000
    assert stats["enp34s0"][0].rx == 1000
    assert stats["enp34s0"][0].ts == 51

    del interfaces._interface_by_name["eno1"]
    interfaces._cleanup_statistics()
    assert "eno1" not in interfaces._statistics_by_name
    assert "enp34s0" in interfaces._statistics_by_name

    throws = False
    try:
        s = interfaces.get_statistics("enp34s0")
        assert s == interfaces._statistics_by_name["enp34s0"]
    except Exception:
        throws = True
    assert not throws

    try:
        interfaces.get_statistics("foobar")
    except UnknownInterfaceError as e:
        assert "foobar" in e.message
        throws = True
    assert throws


def test_get_speed() -> None:

    from gravel.controllers.resources.ifaces import _get_speed

    s = _get_speed("")
    assert s == 0
    s = _get_speed("1bit/s")
    assert s == 1
    s = _get_speed("1Kbit/s")
    assert s == 1000
    s = _get_speed("1Mbit/s")
    assert s == 1000000
    s = _get_speed("1Gbit/s")
    assert s == 1000000000

    throws = False
    try:
        _get_speed("foobar")
    except ValueError:
        throws = True
    assert throws

    throws = False
    try:
        _get_speed("mbit/s")
    except ValueError:
        throws = True
    assert throws
