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

import os
from typing import List, Optional, Tuple

import pytest
from pyfakefs import fake_filesystem
from pytest_mock import MockerFixture

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.mark.asyncio
async def test_network(
    mocker: MockerFixture,
    fs: fake_filesystem.FakeFilesystem,
) -> None:
    async def mock_restart_network(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        assert cmd == ["systemctl", "restart", "network.service"]
        return 0, None, None

    mocker.patch(
        "gravel.controllers.resources.network.aqr_run_cmd",
        new=mock_restart_network,
    )

    from gravel.controllers.resources.network import (
        InterfaceConfigModel,
        InterfaceModel,
        Network,
        RouteModel,
    )

    fs.create_dir(
        "/sys/devices/pci0000:00/0000:00:02.0/0000:01:00.0/net/enp1s0"
    )
    fs.create_symlink(
        "/sys/class/net/enp1s0/device",
        "/sys/devices/pci0000:00/0000:00:02.0/0000:01:00.0/net/enp1s0",
    )
    fs.create_dir("/sys/class/net/virbr0")

    fs.add_real_file(
        source_path=os.path.join(DATA_DIR, "ifcfg-eth0"),
        target_path="/etc/sysconfig/network/ifcfg-eth0",
    )
    fs.create_file("/etc/sysconfig/network/ifcfg-eth0~")
    fs.create_file("/etc/sysconfig/network/ifcfg-eth0.rpmsave")
    fs.create_file("/etc/sysconfig/network/ifcfg-lo")
    fs.add_real_file(
        source_path=os.path.join(DATA_DIR, "config"),
        target_path="/etc/sysconfig/network/config",
    )

    network = Network(5.0)
    assert await network._should_tick()

    await network._do_tick()

    ifaces = network.interfaces
    assert len(ifaces) > 0

    assert "eth0" in ifaces
    assert ifaces["eth0"].name == "eth0"
    assert ifaces["eth0"].config.bootproto == "dhcp"
    assert ifaces["eth0"].config.ipaddr == ""
    assert ifaces["eth0"].config.bonding_slaves == []

    assert "eth0~" not in ifaces
    assert "eth0.rpmsave" not in ifaces

    assert "enp1s0" in ifaces
    assert ifaces["enp1s0"].config is None

    assert "virbr0" not in ifaces

    assert "lo" not in ifaces

    assert network.nameservers == []

    assert network.routes == []

    ifaces["bond0"] = InterfaceModel(
        name="bond0",
        config=InterfaceConfigModel(
            bootproto="static",
            ipaddr="192.168.121.10/24",
            bonding_slaves=["enp1s0", "enp2s0"],
        ),
    )
    await network.apply_config(
        ifaces,
        ["8.8.8.8", "1.1.1.1"],
        routes=[
            RouteModel(destination="default", gateway="192.168.121.1"),
            RouteModel(destination="192.168.0.0/16", interface="bond0"),
        ],
    )

    ifaces = network.interfaces
    assert "bond0" in ifaces
    assert os.path.exists("/etc/sysconfig/network/ifcfg-enp1s0")
    assert os.path.exists("/etc/sysconfig/network/ifcfg-enp2s0")
    assert network.nameservers == ["8.8.8.8", "1.1.1.1"]
    assert os.path.exists("/etc/sysconfig/network/routes")
    assert os.path.exists("/etc/sysconfig/network/ifroute-bond0")
    assert len(network.routes) == 2
