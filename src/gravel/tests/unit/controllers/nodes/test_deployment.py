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
# pyright: reportUnknownVariableType=false

from typing import Awaitable, Callable, List, Optional, cast
import pytest
from pytest_mock import MockerFixture

from gravel.controllers.gstate import GlobalState
from gravel.controllers.nodes.deployment import DeploymentDisksConfig


@pytest.mark.asyncio
async def test_state(mocker: MockerFixture, gstate: GlobalState):
    from gravel.controllers.nodes.deployment import (
        DeploymentState,
        NodeStageEnum,
        DeploymentErrorEnum,
    )

    mocker.patch.object(DeploymentState, "_load_stage")
    mocker.patch.object(DeploymentState, "_save_stage")

    state = DeploymentState(gstate)
    assert state.nostage
    assert not state.bootstrapping
    assert not state.deployed
    assert not state.joining
    assert not state.error
    assert not state.ready
    assert state.stage == NodeStageEnum.NONE
    assert state.can_start()

    state.mark_bootstrap()
    assert state.bootstrapping
    assert not state.nostage
    assert not state.deployed
    assert not state.joining
    assert not state.error
    assert not state.ready
    assert state.stage == NodeStageEnum.BOOTSTRAPPING
    assert not state.can_start()

    state.mark_deployed()
    assert state.deployed
    assert not state.nostage
    assert not state.bootstrapping
    assert not state.joining
    assert not state.error
    assert not state.ready
    assert state.stage == NodeStageEnum.DEPLOYED
    assert state.can_start()

    state.mark_join()
    assert state.joining
    assert not state.nostage
    assert not state.bootstrapping
    assert not state.deployed
    assert not state.error
    assert not state.ready
    assert state.stage == NodeStageEnum.JOINING
    assert not state.can_start()

    state.mark_ready()
    assert state.ready
    assert not state.nostage
    assert not state.bootstrapping
    assert not state.deployed
    assert not state.joining
    assert not state.error
    assert state.stage == NodeStageEnum.READY
    assert state.can_start()

    state.mark_error(code=DeploymentErrorEnum.UNKNOWN_ERROR, msg="foobar")
    assert state.error
    assert not state.nostage
    assert not state.bootstrapping
    assert not state.deployed
    assert not state.joining
    assert not state.ready
    assert state.stage == NodeStageEnum.ERROR
    assert state.error_what.code == DeploymentErrorEnum.UNKNOWN_ERROR
    assert state.error_what.msg == "foobar"
    assert not state.can_start()


@pytest.mark.asyncio
async def test_deployment_progress(mocker: MockerFixture, gstate: GlobalState):

    from gravel.controllers.nodes.conn import ConnMgr
    from gravel.controllers.nodes.deployment import (
        NodeDeployment,
        DeploymentErrorEnum,
        ProgressEnum,
    )

    fake_connmgr: ConnMgr = cast(ConnMgr, mocker.MagicMock())
    deployment = NodeDeployment(gstate, fake_connmgr)

    # no bootstrapper, nostage
    assert deployment.progress == 0

    # test actual progress
    deployment.state.mark_bootstrap()
    assert deployment.progress == 0  # no bootstrapper set

    deployment._bootstrapper = mocker.MagicMock()
    assert deployment._bootstrapper is not None

    # we need to do creative mocking for a property that happens to be an
    # attribute on a mock object itself.
    #  https://docs.python.org/3/library/unittest.mock.html#unittest.mock.PropertyMock
    fake_progress = mocker.PropertyMock()
    type(deployment._bootstrapper).progress = fake_progress  # type: ignore

    fake_progress.return_value = 0

    # progress is set at NONE
    assert deployment.progress == 0

    deployment._progress = ProgressEnum.PREPARING
    assert deployment.progress == 25

    deployment._progress = ProgressEnum.PERFORMING
    assert deployment._bootstrapper.progress == 0
    assert deployment.progress == 25
    fake_progress.return_value = 100
    assert deployment._bootstrapper.progress == 100
    assert deployment.progress == 80

    deployment._progress = ProgressEnum.ASSIMILATING
    assert deployment.progress == 90

    deployment._progress = ProgressEnum.DONE
    assert deployment.progress == 100

    # deployed stage
    deployment.state.mark_deployed()
    assert deployment.progress == 100

    # error state
    deployment.state.mark_error(DeploymentErrorEnum.UNKNOWN_ERROR, "foobar")
    assert deployment.progress == 0


@pytest.mark.asyncio
async def test_deploy(mocker: MockerFixture, gstate: GlobalState):
    from gravel.controllers.nodes.conn import ConnMgr
    from gravel.controllers.nodes.deployment import (
        NodeDeployment,
        DeploymentConfig,
    )
    from gravel.controllers.nodes.bootstrap import Bootstrap
    from gravel.controllers.orch.orchestrator import Orchestrator
    from gravel.controllers.nodes.systemdisk import SystemDisk

    def mock_devices_assimilated(
        cls, hostname: str, devs: List[str]  # type: ignore
    ):
        return True

    async def mock_bootstrap(
        cls,  # type: ignore
        address: str,
        cb: Callable[[bool, Optional[str]], Awaitable[None]],
    ) -> None:
        assert address == "127.0.0.1"
        await cb(True, None)

    called_hostname_with: Optional[str] = None
    called_ntp_with: Optional[str] = None
    called_assimilate_with: List[str] = []
    called_check_host_exists_with: Optional[str] = None

    async def mock_set_hostname(hostname: str) -> None:
        nonlocal called_hostname_with
        called_hostname_with = hostname

    async def mock_set_ntpaddr(ntp_addr: str) -> None:
        nonlocal called_ntp_with
        called_ntp_with = ntp_addr

    def mock_assimilate_devices(
        cls, host: str, devices: List[str]  # type: ignore
    ) -> None:
        nonlocal called_assimilate_with
        called_assimilate_with.extend(devices)

    def mock_host_exists(cls, hostname: str) -> bool:  # type: ignore
        nonlocal called_check_host_exists_with
        called_check_host_exists_with = hostname
        return True

    fake_connmgr: ConnMgr = cast(ConnMgr, mocker.MagicMock())
    deployment = NodeDeployment(gstate, fake_connmgr)
    deployment._prepare_etcd = mocker.AsyncMock()
    deployment._set_hostname = mock_set_hostname
    deployment._set_ntp_addr = mock_set_ntpaddr

    mocker.patch.object(
        Bootstrap, "bootstrap", new=mock_bootstrap  # type: ignore
    )
    mocker.patch.object(
        Orchestrator,
        "assimilate_devices",
        new=mock_assimilate_devices,  # type: ignore
    )
    mocker.patch.object(
        Orchestrator,
        "devices_assimilated",
        new=mock_devices_assimilated,  # type: ignore
    )
    mocker.patch.object(
        Orchestrator, "host_exists", new=mock_host_exists  # type: ignore
    )
    mocker.patch.object(SystemDisk, "create")
    mocker.patch.object(SystemDisk, "enable")

    called_postbootstrap = False
    called_finisher = False

    async def postbootstrap_cb(res: bool, errstr: Optional[str]) -> None:
        assert res
        assert not errstr
        nonlocal called_postbootstrap
        called_postbootstrap = True

    async def finisher_cb(res: bool, errstr: Optional[str]) -> None:
        assert res
        assert not errstr
        nonlocal called_finisher
        called_finisher = True

    disks = DeploymentDisksConfig(
        system="/dev/foobar", storage=["/dev/bar", "/dev/baz"]
    )

    await deployment.deploy(
        DeploymentConfig(
            hostname="foobar",
            address="127.0.0.1",
            token="myfancytoken",
            ntp_addr="my.ntp.test",
            disks=disks,
        ),
        post_bootstrap_cb=postbootstrap_cb,
        finisher=finisher_cb,
    )

    assert called_postbootstrap
    assert called_finisher
    assert called_ntp_with and called_ntp_with == "my.ntp.test"
    assert called_hostname_with and called_hostname_with == "foobar"
    assert (
        called_check_host_exists_with
        and called_check_host_exists_with == "foobar"
    )
    assert "/dev/bar" in called_assimilate_with
    assert "/dev/baz" in called_assimilate_with


@pytest.mark.asyncio
async def test_finish_deployment(mocker: MockerFixture, gstate: GlobalState):
    from gravel.controllers.nodes.conn import ConnMgr
    from gravel.controllers.nodes.deployment import NodeDeployment

    fake_connmgr: ConnMgr = cast(ConnMgr, mocker.MagicMock())
    deployment = NodeDeployment(gstate, fake_connmgr)
    deployment.state.mark_bootstrap()
    deployment.finish_deployment()
    assert deployment.state.deployed
