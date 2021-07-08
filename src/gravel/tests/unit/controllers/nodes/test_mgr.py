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

# pyright: reportPrivateUsage=false, reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false

from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
import pytest
from pytest_mock import MockerFixture
from pyfakefs import fake_filesystem

from gravel.controllers.gstate import GlobalState
from gravel.controllers.nodes.mgr import DeployParamsModel


def test_fail_ctor(
    gstate: GlobalState, fs: fake_filesystem.FakeFilesystem
) -> None:

    from gravel.controllers.nodes.mgr import NodeMgr, NodeError

    if fs.exists("/etc/aquarium/node.json"):
        fs.remove("/etc/aquarium/node.json")
    fs.create_dir("/etc/aquarium/node.json")
    throws = False
    try:
        NodeMgr(gstate)
    except NodeError:
        throws = True
    except Exception:
        assert False
    assert throws
    # clean up
    fs.rmdir("/etc/aquarium/node.json")


def test_ctor(
    gstate: GlobalState, fs: fake_filesystem.FakeFilesystem
) -> None:
    from gravel.controllers.nodes.mgr import NodeMgr
    NodeMgr(gstate)
    assert fs.exists("/etc/aquarium/node.json")

    # clean up
    for f in fs.listdir("/etc/aquarium"):
        fs.remove(f"/etc/aquarium/{f}")


def test_init_state_fail(
    gstate: GlobalState, fs: fake_filesystem.FakeFilesystem
) -> None:

    from gravel.controllers.nodes.mgr import NodeMgr, NodeError

    if fs.exists("/etc/aquarium/node.json"):
        fs.remove("/etc/aquarium/node.json")

    nodemgr = NodeMgr(gstate)
    assert fs.exists("/etc/aquarium/node.json")
    for f in fs.listdir("/etc/aquarium"):
        fs.remove(f"/etc/aquarium/{f}")
    assert fs.exists("/etc/aquarium")
    fs.rmdir("/etc/aquarium")
    fs.create_dir("/etc/aquarium", perm_bits=0o500)

    throws = False
    try:
        nodemgr._init_state()
    except NodeError:
        throws = True
    assert throws

    # clean up
    for f in fs.listdir("/etc/aquarium"):
        fs.remove(f"/etc/aquarium/{f}")
    fs.rmdir("/etc/aquarium")


@pytest.mark.asyncio
async def test_mgr_start(
    gstate: GlobalState,
    fs: fake_filesystem.FakeFilesystem,
    mocker: MockerFixture
) -> None:

    from gravel.controllers.nodes.mgr import NodeMgr, NodeError, NodeStateModel
    from gravel.controllers.nodes.deployment import NodeStageEnum

    nodemgr = NodeMgr(gstate)
    assert nodemgr._state
    assert nodemgr.deployment_state.can_start()

    orig = nodemgr.deployment_state.can_start
    nodemgr.deployment_state.can_start = mocker.MagicMock(return_value=False)
    throws = False
    try:
        await nodemgr.start()
    except NodeError as e:
        assert "unstartable" in e.message
        throws = True
    assert throws
    nodemgr.deployment_state.can_start = orig

    called_prepare = False

    async def mock_prepare() -> None:
        nonlocal called_prepare
        called_prepare = True

    nodemgr._deployment._state._stage = NodeStageEnum.NONE
    nodemgr._node_prepare = mock_prepare
    await nodemgr.start()
    assert called_prepare

    nodemgr._deployment._state._stage = NodeStageEnum.READY
    nodemgr._state = NodeStateModel(
        uuid="bba35d93-d4a5-48b3-804b-99c406555c89",
        address="1.2.3.4",
        hostname="foobar"
    )

    called_etcd_spawn = False
    called_start_ceph = False
    called_node_start = False

    async def mock_spawn_etcd(
        gstate: GlobalState,
        new: bool,
        token: Optional[str],
        hostname: str,
        address: str,
        initial_cluster: Optional[str] = None
    ) -> None:
        assert not new
        assert token is None
        assert hostname == "foobar"
        assert address == "1.2.3.4"
        assert initial_cluster is None
        nonlocal called_etcd_spawn
        called_etcd_spawn = True

    async def mock_start_ceph() -> None:
        nonlocal called_start_ceph
        called_start_ceph = True

    async def mock_node_start() -> None:
        nonlocal called_node_start
        called_node_start = True

    mocker.patch(
        "gravel.controllers.nodes.mgr.spawn_etcd", new=mock_spawn_etcd
    )
    # save orig state
    orig_start_ceph = nodemgr._start_ceph
    orig_node_start = nodemgr._node_start
    nodemgr._start_ceph = mock_start_ceph
    nodemgr._node_start = mock_node_start

    await nodemgr.start()
    assert called_etcd_spawn
    assert called_start_ceph
    assert called_node_start

    # restore orig state
    nodemgr._start_ceph = orig_start_ceph
    nodemgr._node_start = orig_node_start


@pytest.mark.asyncio
async def test_obtain_images(
    gstate: GlobalState, mocker: MockerFixture
) -> None:

    called_cephadm_pull_images = False
    called_etcd_pull_image = False

    async def mock_cephadm_pull_img() -> None:
        nonlocal called_cephadm_pull_images
        called_cephadm_pull_images = True

    async def mock_etcd_pull_img(gstate: GlobalState) -> None:
        nonlocal called_etcd_pull_image
        called_etcd_pull_image = True

    mocker.patch(
        "gravel.controllers.nodes.mgr.etcd_pull_image", new=mock_etcd_pull_img
    )
    orig_cephadm_pull_img = gstate.cephadm.pull_images
    gstate.cephadm.pull_images = mock_cephadm_pull_img

    from gravel.controllers.nodes.mgr import NodeMgr

    nodemgr = NodeMgr(gstate)
    ret = await nodemgr._obtain_images()
    assert ret
    assert called_cephadm_pull_images
    assert called_etcd_pull_image

    from gravel.cephadm.cephadm import CephadmError

    called_cephadm_pull_images = False

    async def fail_cephadm_pull_img() -> None:
        nonlocal called_cephadm_pull_images
        called_cephadm_pull_images = True
        raise CephadmError("foobar")

    gstate.cephadm.pull_images = fail_cephadm_pull_img
    ret = await nodemgr._obtain_images()
    assert not ret
    assert called_cephadm_pull_images

    from gravel.controllers.nodes.etcd import ContainerFetchError

    called_etcd_pull_image_fail = False

    async def fail_etcd_pull_img(gstate: GlobalState) -> None:
        nonlocal called_etcd_pull_image_fail
        called_etcd_pull_image_fail = True
        raise ContainerFetchError("barbaz")

    mocker.patch(
        "gravel.controllers.nodes.mgr.etcd_pull_image", new=fail_etcd_pull_img
    )
    gstate.cephadm.pull_images = mocker.AsyncMock()

    ret = await nodemgr._obtain_images()
    assert not ret
    assert called_etcd_pull_image_fail

    gstate.cephadm.pull_images = orig_cephadm_pull_img


@pytest.mark.asyncio
async def test_node_start(
    gstate: GlobalState,
    mocker: MockerFixture,
    fs: fake_filesystem.FakeFilesystem
) -> None:

    from gravel.controllers.nodes.mgr import (
        NodeMgr,
        NodeStateModel,
        NodeInitStage
    )
    from gravel.controllers.nodes.deployment import NodeStageEnum

    nodemgr = NodeMgr(gstate)
    nodemgr._state = NodeStateModel(
        uuid="bba35d93-d4a5-48b3-804b-99c406555c89",
        address="1.2.3.4",
        hostname="foobar"
    )
    nodemgr._deployment._state._stage = NodeStageEnum.READY

    nodemgr._obtain_state = mocker.AsyncMock()
    nodemgr._load = mocker.AsyncMock()
    nodemgr._incoming_msg_task = mocker.AsyncMock()
    nodemgr._connmgr.start_receiving = mocker.MagicMock()

    await nodemgr._node_start()

    assert nodemgr._init_stage == NodeInitStage.STARTED
    nodemgr._obtain_state.assert_called_once()  # type: ignore
    nodemgr._load.assert_called_once()  # type: ignore
    nodemgr._incoming_msg_task.assert_called_once()  # type: ignore
    nodemgr._connmgr.start_receiving.assert_called_once()  # type: ignore


@pytest.mark.asyncio
async def test_start_ceph(gstate: GlobalState, mocker: MockerFixture) -> None:

    from gravel.controllers.nodes.mgr import NodeMgr, NodeError

    called = False

    async def mock_call(
        cmd: List[str]
    ) -> Tuple[int, Optional[str], Optional[str]]:
        nonlocal called
        called = True
        assert cmd[0] == "systemctl"
        assert cmd[1] == "start"
        assert cmd[2] == "ceph.target"
        return 0, None, None

    mocker.patch("gravel.controllers.nodes.mgr.aqr_run_cmd", new=mock_call)

    nodemgr = NodeMgr(gstate)
    await nodemgr._start_ceph()
    assert called

    called = False

    async def fail_call(
        cmd: List[str]
    ) -> Tuple[int, Optional[str], Optional[str]]:
        nonlocal called
        called = True
        return 1, None, "oops"

    mocker.patch("gravel.controllers.nodes.mgr.aqr_run_cmd", new=fail_call)

    throwed = False
    try:
        await nodemgr._start_ceph()
    except NodeError as e:
        assert "oops" in e.message
        throwed = True
    assert called
    assert throwed


def test_node_shutdown(gstate: GlobalState, mocker: MockerFixture) -> None:

    from gravel.controllers.nodes.mgr import NodeMgr, NodeInitStage

    class FakeTask:
        called = False

        def cancel(self) -> None:
            self.called = True

    nodemgr = NodeMgr(gstate)
    nodemgr._incoming_task = FakeTask()  # type: ignore
    nodemgr._init_stage = NodeInitStage.NONE
    nodemgr._node_shutdown()
    assert nodemgr._init_stage == NodeInitStage.STOPPING
    assert nodemgr._incoming_task.called


def test_generate_token(gstate: GlobalState) -> None:

    from gravel.controllers.nodes.mgr import NodeMgr

    nodemgr = NodeMgr(gstate)
    token = nodemgr._generate_token()
    assert len(token) > 0
    res = token.split("-")
    assert len(res) == 4
    for s in res:
        assert len(s) == 4


@pytest.mark.asyncio
async def test_join_checks(gstate: GlobalState) -> None:

    from gravel.controllers.nodes.mgr import (
        NodeMgr,
        NodeCantJoinError,
        NodeNotStartedError,
        NodeError,
        NodeInitStage,
        JoinParamsModel
    )

    nodemgr = NodeMgr(gstate)

    throws = False
    nodemgr._init_stage = NodeInitStage.NONE
    try:
        await nodemgr.join(
            "1.2.3.4",
            "751b-51fd-10d7-f7b4",
            JoinParamsModel(hostname="foobar")
        )
    except NodeNotStartedError:
        throws = True
    assert throws

    throws = False
    nodemgr._init_stage = NodeInitStage.STARTED
    try:
        await nodemgr.join(
            "1.2.3.4",
            "751b-51fd-10d7-f7b4",
            JoinParamsModel(hostname="foobar")
        )
    except NodeCantJoinError:
        throws = True
    assert throws

    throws = False
    nodemgr._init_stage = NodeInitStage.AVAILABLE
    try:
        await nodemgr.join(
            "1.2.3.4",
            "751b-51fd-10d7-f7b4",
            JoinParamsModel(hostname="")
        )
    except NodeError as e:
        throws = True
        assert "hostname" in e.message
    assert throws


@pytest.mark.asyncio
async def test_join_check_disk_solution(
    gstate: GlobalState, mocker: MockerFixture
) -> None:

    from gravel.controllers.nodes.mgr import (
        NodeMgr,
        NodeCantJoinError,
        NodeStateModel,
        NodeInitStage,
        JoinParamsModel
    )
    from gravel.controllers.nodes.disks import DiskSolution

    nodemgr = NodeMgr(gstate)
    nodemgr._state = NodeStateModel(
        uuid="bba35d93-d4a5-48b3-804b-99c406555c89",
        address="1.2.3.4",
        hostname="foobar"
    )
    nodemgr._init_stage = NodeInitStage.AVAILABLE

    def empty_solution(gstate: GlobalState) -> DiskSolution:
        return DiskSolution()

    mocker.patch(
        "gravel.controllers.nodes.disks.Disks.gen_solution", new=empty_solution
    )

    throws = False
    try:
        await nodemgr.join(
            "1.2.3.4",
            "751b-51fd-10d7-f7b4",
            JoinParamsModel(hostname="foobar")
        )
    except NodeCantJoinError as e:
        assert e.message == "no disk deployment solution found"
        throws = True
    assert throws

    def fail_solution(gstate: GlobalState) -> DiskSolution:
        return DiskSolution(possible=True)

    mocker.patch(
        "gravel.controllers.nodes.disks.Disks.gen_solution", new=fail_solution
    )

    throws = False
    try:
        await nodemgr.join(
            "1.2.3.4",
            "751b-51fd-10d7-f7b4",
            JoinParamsModel(hostname="foobar")
        )
    except AssertionError:
        throws = True
    assert throws


@pytest.mark.asyncio
async def test_join(gstate: GlobalState, mocker: MockerFixture) -> None:

    from uuid import UUID
    from gravel.controllers.nodes.mgr import (
        NodeMgr,
        NodeStateModel,
        NodeInitStage,
        JoinParamsModel
    )
    from gravel.controllers.nodes.disks import DiskSolution, DiskModel
    from gravel.controllers.nodes.deployment import DeploymentDisksConfig

    def mock_solution(gstate: GlobalState) -> DiskSolution:
        return DiskSolution(
            systemdisk=DiskModel(path="/dev/foo", size=1000),
            storage=[
                DiskModel(path="/dev/bar", size=2000),
                DiskModel(path="/dev/baz", size=2000)
            ],
            storage_size=4000,
            possible=True
        )

    async def mock_join(
        leader_address: str,
        token: str,
        uuid: UUID,
        hostname: str,
        address: str,
        disks: DeploymentDisksConfig
    ) -> bool:
        assert leader_address == "10.1.2.3"
        assert token == "751b-51fd-10d7-f7b4"
        assert str(uuid) == "bba35d93-d4a5-48b3-804b-99c406555c89"
        assert hostname == "foobar"
        assert address == "1.2.3.4"
        assert disks.system == "/dev/foo"
        assert len(disks.storage) == 2
        assert "/dev/bar" in disks.storage
        assert "/dev/baz" in disks.storage
        return True

    async def fail_join(
        leader_address: str,
        token: str,
        uuid: UUID,
        hostname: str,
        address: str,
        disks: DeploymentDisksConfig
    ) -> bool:
        return False

    async def throw_join(
        leader_address: str,
        token: str,
        uuid: UUID,
        hostname: str,
        address: str,
        disks: DeploymentDisksConfig
    ) -> bool:
        raise Exception()

    mocker.patch(
        "gravel.controllers.nodes.disks.Disks.gen_solution", new=mock_solution
    )

    nodemgr = NodeMgr(gstate)
    nodemgr._state = NodeStateModel(
        uuid="bba35d93-d4a5-48b3-804b-99c406555c89",
        address="1.2.3.4",
        hostname="foobar"
    )
    nodemgr._init_stage = NodeInitStage.AVAILABLE

    nodemgr._deployment.join = throw_join
    throws = False
    try:
        await nodemgr.join(
            "10.1.2.3",
            "751b-51fd-10d7-f7b4",
            JoinParamsModel(hostname="foobar")
        )
    except Exception:
        throws = True
    assert throws

    nodemgr._deployment.join = fail_join
    res = await nodemgr.join(
        "10.1.2.3",
        "751b-51fd-10d7-f7b4",
        JoinParamsModel(hostname="foobar")
    )
    assert not res

    nodemgr._save_state = mocker.AsyncMock()
    nodemgr._node_start = mocker.AsyncMock()
    nodemgr._deployment.join = mock_join
    res = await nodemgr.join(
        "10.1.2.3",
        "751b-51fd-10d7-f7b4",
        JoinParamsModel(hostname="foobar")
    )
    assert res
    assert nodemgr._token == "751b-51fd-10d7-f7b4"
    nodemgr._save_state.assert_called_once()  # type: ignore
    nodemgr._node_start.assert_called_once()  # type: ignore


@pytest.mark.asyncio
async def test_deploy_checks(gstate: GlobalState) -> None:

    from gravel.controllers.nodes.mgr import (
        NodeMgr,
        NodeInitStage,
        NodeNotStartedError,
        NodeCantDeployError,
        NodeStateModel,
        DeployParamsModel
    )
    from gravel.controllers.nodes.deployment import NodeStageEnum

    nodemgr = NodeMgr(gstate)
    nodemgr._state = NodeStateModel(
        uuid="bba35d93-d4a5-48b3-804b-99c406555c89",
        address="1.2.3.4",
        hostname="foobar"
    )

    nodemgr._init_stage = NodeInitStage.NONE
    throws = False
    try:
        await nodemgr.deploy(
            DeployParamsModel(hostname="barbaz", ntpaddr="my.ntp.addr")
        )
    except NodeNotStartedError:
        throws = True
    assert throws

    nodemgr._init_stage = NodeInitStage.PREPARE
    throws = False
    try:
        await nodemgr.deploy(
            DeployParamsModel(hostname="barbaz", ntpaddr="my.ntp.addr")
        )
    except NodeNotStartedError:
        throws = True
    assert throws

    nodemgr._init_stage = NodeInitStage.AVAILABLE
    nodemgr._deployment._state._stage = NodeStageEnum.ERROR
    throws = False
    try:
        await nodemgr.deploy(
            DeployParamsModel(hostname="barbaz", ntpaddr="my.ntp.addr")
        )
    except NodeCantDeployError:
        throws = True
    assert throws

    nodemgr._deployment._state._stage = NodeStageEnum.NONE
    throws = False
    try:
        await nodemgr.deploy(
            DeployParamsModel(hostname="", ntpaddr="my.ntp.addr")
        )
    except NodeCantDeployError as e:
        assert e.message == "missing hostname parameter"
        throws = True
    assert throws

    throws = False
    try:
        await nodemgr.deploy(
            DeployParamsModel(hostname="barbaz", ntpaddr="")
        )
    except NodeCantDeployError as e:
        assert e.message == "missing ntp server address"
        throws = True
    assert throws


@pytest.mark.asyncio
async def test_deploy_check_disk_solution(
    gstate: GlobalState, mocker: MockerFixture
) -> None:
    from gravel.controllers.nodes.mgr import (
        NodeMgr,
        NodeInitStage,
        NodeStateModel,
        NodeCantDeployError
    )
    from gravel.controllers.nodes.disks import DiskSolution

    nodemgr = NodeMgr(gstate)
    nodemgr._state = NodeStateModel(
        uuid="bba35d93-d4a5-48b3-804b-99c406555c89",
        address="1.2.3.4",
        hostname="foobar"
    )
    nodemgr._init_stage = NodeInitStage.AVAILABLE

    def empty_solution(gstate: GlobalState) -> DiskSolution:
        return DiskSolution()

    def fail_solution(gstate: GlobalState) -> DiskSolution:
        return DiskSolution(possible=True)

    mocker.patch(
        "gravel.controllers.nodes.disks.Disks.gen_solution", new=empty_solution
    )
    throws = False
    try:
        await nodemgr.deploy(
            DeployParamsModel(hostname="barbaz", ntpaddr="my.ntp.addr")
        )
    except NodeCantDeployError as e:
        assert e.message == "no possible deployment solution found"
        throws = True
    assert throws

    mocker.patch(
        "gravel.controllers.nodes.disks.Disks.gen_solution", new=fail_solution
    )
    throws = False
    try:
        await nodemgr.deploy(
            DeployParamsModel(hostname="barbaz", ntpaddr="my.ntp.addr")
        )
    except AssertionError:
        throws = True
    assert throws


@pytest.mark.asyncio
async def test_deploy(gstate: GlobalState, mocker: MockerFixture) -> None:

    from gravel.controllers.nodes.mgr import (
        NodeMgr,
        NodeInitStage,
        NodeStateModel
    )
    from gravel.controllers.nodes.disks import DiskSolution, DiskModel
    from gravel.controllers.nodes.deployment import DeploymentConfig

    called_mock_deploy = False

    def mock_solution(gstate: GlobalState) -> DiskSolution:
        return DiskSolution(
            systemdisk=DiskModel(path="/dev/foo", size=1000),
            storage=[
                DiskModel(path="/dev/bar", size=2000),
                DiskModel(path="/dev/baz", size=2000)
            ],
            storage_size=4000,
            possible=True
        )

    async def mock_deploy(
        config: DeploymentConfig,
        post_bootstrap_cb: Callable[[bool, Optional[str]], Awaitable[None]],
        finisher: Callable[[bool, Optional[str]], Awaitable[None]]
    ) -> None:

        import inspect

        nonlocal called_mock_deploy
        called_mock_deploy = True

        assert config.hostname == "barbaz"
        assert config.address == "1.2.3.4"
        assert config.token == "751b-51fd-10d7-f7b4"
        assert config.ntp_addr == "my.ntp.addr"
        assert config.disks.system == "/dev/foo"
        assert len(config.disks.storage) == 2
        assert "/dev/bar" in config.disks.storage
        assert "/dev/baz" in config.disks.storage
        assert post_bootstrap_cb is not None
        assert finisher is not None
        assert inspect.iscoroutinefunction(post_bootstrap_cb)
        assert inspect.iscoroutinefunction(finisher)

    mocker.patch(
        "gravel.controllers.nodes.disks.Disks.gen_solution", new=mock_solution
    )

    nodemgr = NodeMgr(gstate)
    nodemgr._state = NodeStateModel(
        uuid="bba35d93-d4a5-48b3-804b-99c406555c89",
        address="1.2.3.4",
        hostname="foobar"
    )
    nodemgr._init_stage = NodeInitStage.AVAILABLE

    nodemgr._generate_token = mocker.MagicMock(
        return_value="751b-51fd-10d7-f7b4"
    )
    nodemgr._save_token = mocker.AsyncMock()
    nodemgr._save_ntp_addr = mocker.AsyncMock()
    nodemgr._deployment.deploy = mock_deploy

    await nodemgr.deploy(
        DeployParamsModel(hostname="barbaz", ntpaddr="my.ntp.addr")
    )

    assert called_mock_deploy
    assert nodemgr._token == "751b-51fd-10d7-f7b4"
    assert nodemgr._state.hostname == "barbaz"
    nodemgr._save_token.assert_called_once()  # type: ignore
    nodemgr._save_ntp_addr.assert_called_once_with("my.ntp.addr")  # type: ignore


@pytest.mark.asyncio
async def test_postbootstrap_config(
    mocker: MockerFixture,
    gstate: GlobalState
) -> None:

    config_keys: Dict[str, Tuple[str, str]] = {}

    def config_set(cls: Any, who: str, name: str, value: str) -> bool:
        config_keys[name] = (who, value)
        return True

    def expect_key(who: str, name: str, value: str) -> None:
        assert name in config_keys
        scope, val = config_keys[name]
        assert scope == who
        assert val == value

    from gravel.controllers.nodes.mgr import NodeMgr
    from gravel.controllers.orch.ceph import Mon
    mocker.patch.object(NodeMgr, "_init_state")
    mocker.patch.object(Mon, "config_set", new=config_set)
    mocker.patch.object(Mon, "call")
    mocker.patch.object(Mon, "set_default_ruleset")  # ignore default ruleset

    mgr = NodeMgr(gstate)
    await mgr._post_bootstrap_config()

    expect_key("global", "mon_allow_pool_size_one", "true")
    expect_key("global", "mon_warn_on_pool_no_redundancy", "false")
    expect_key("mgr", "mgr/cephadm/manage_etc_ceph_ceph_conf", "true")
    expect_key("global", "auth_allow_insecure_global_id_reclaim", "false")
