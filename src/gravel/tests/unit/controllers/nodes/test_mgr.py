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

from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, cast
import pytest
from pytest_mock import MockerFixture
from pyfakefs import fake_filesystem

from gravel.controllers.gstate import GlobalState
from gravel.controllers.nodes.conn import IncomingConnection
from gravel.controllers.nodes.messages import MessageModel
from gravel.controllers.nodes.mgr import DeployParamsModel, NodeMgr


@pytest.fixture
def nodemgr(gstate: GlobalState) -> NodeMgr:

    from gravel.controllers.nodes.mgr import NodeStateModel

    nodemgr = NodeMgr(gstate)
    nodemgr._state = NodeStateModel(
        uuid="bba35d93-d4a5-48b3-804b-99c406555c89",
        address="1.2.3.4",
        hostname="foobar",
    )
    yield nodemgr


def test_fail_ctor(
    gstate: GlobalState, fs: fake_filesystem.FakeFilesystem
) -> None:

    from gravel.controllers.nodes.mgr import NodeError

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


def test_ctor(gstate: GlobalState, fs: fake_filesystem.FakeFilesystem) -> None:

    NodeMgr(gstate)
    assert fs.exists("/etc/aquarium/node.json")

    # clean up
    for f in fs.listdir("/etc/aquarium"):
        fs.remove(f"/etc/aquarium/{f}")


def test_init_state_fail(
    gstate: GlobalState, fs: fake_filesystem.FakeFilesystem
) -> None:

    from gravel.controllers.nodes.mgr import NodeError

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
    mocker: MockerFixture,
) -> None:

    from gravel.controllers.nodes.mgr import NodeError, NodeStateModel
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

    nodemgr._deployment._state._stage = NodeStageEnum.NONE
    nodemgr._node_prepare = mocker.AsyncMock()
    await nodemgr.start()
    nodemgr._node_prepare.assert_called_once()  # type: ignore

    nodemgr._deployment._state._stage = NodeStageEnum.READY
    nodemgr._state = NodeStateModel(
        uuid="bba35d93-d4a5-48b3-804b-99c406555c89",
        address="1.2.3.4",
        hostname="foobar",
    )

    called_etcd_spawn = False

    async def mock_spawn_etcd(
        gstate: GlobalState,
        new: bool,
        token: Optional[str],
        hostname: str,
        address: str,
        initial_cluster: Optional[str] = None,
    ) -> None:
        assert not new
        assert token is None
        assert hostname == "foobar"
        assert address == "1.2.3.4"
        assert initial_cluster is None
        nonlocal called_etcd_spawn
        called_etcd_spawn = True

    mocker.patch("gravel.controllers.nodes.mgr.spawn_etcd", new=mock_spawn_etcd)
    nodemgr._start_ceph = mocker.AsyncMock()
    nodemgr._node_start = mocker.AsyncMock()

    await nodemgr.start()
    assert called_etcd_spawn
    nodemgr._start_ceph.assert_called_once()  # type: ignore
    nodemgr._node_start.assert_called_once()  # type: ignore


@pytest.mark.asyncio
async def test_obtain_images(
    gstate: GlobalState, mocker: MockerFixture
) -> None:

    called_etcd_pull_image = False

    async def mock_etcd_pull_img(gstate: GlobalState) -> None:
        nonlocal called_etcd_pull_image
        called_etcd_pull_image = True

    mocker.patch(
        "gravel.controllers.nodes.mgr.etcd_pull_image", new=mock_etcd_pull_img
    )
    orig_cephadm_pull_img = gstate.cephadm.pull_images
    gstate.cephadm.pull_images = mocker.AsyncMock()

    nodemgr = NodeMgr(gstate)
    ret = await nodemgr._obtain_images()
    assert ret
    gstate.cephadm.pull_images.assert_called_once()  # type: ignore
    assert called_etcd_pull_image

    from gravel.cephadm.cephadm import CephadmError

    gstate.cephadm.pull_images = mocker.AsyncMock(
        side_effect=CephadmError("foobar")
    )
    ret = await nodemgr._obtain_images()
    assert not ret
    gstate.cephadm.pull_images.assert_called_once()  # type: ignore

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
    gstate.cephadm.pull_images.assert_called_once()  # type: ignore

    gstate.cephadm.pull_images = orig_cephadm_pull_img


@pytest.mark.asyncio
async def test_node_start(
    gstate: GlobalState,
    mocker: MockerFixture,
    fs: fake_filesystem.FakeFilesystem,
    nodemgr: NodeMgr,
) -> None:

    from gravel.controllers.nodes.mgr import NodeInitStage
    from gravel.controllers.nodes.deployment import NodeStageEnum

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

    from gravel.controllers.nodes.mgr import NodeError

    called = False

    async def mock_call(
        cmd: List[str],
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
        cmd: List[str],
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
        NodeCantJoinError,
        NodeNotStartedError,
        NodeError,
        NodeInitStage,
        JoinParamsModel,
    )

    nodemgr = NodeMgr(gstate)

    throws = False
    nodemgr._init_stage = NodeInitStage.NONE
    try:
        await nodemgr.join(
            "1.2.3.4", "751b-51fd-10d7-f7b4", JoinParamsModel(hostname="foobar")
        )
    except NodeNotStartedError:
        throws = True
    assert throws

    throws = False
    nodemgr._init_stage = NodeInitStage.STARTED
    try:
        await nodemgr.join(
            "1.2.3.4", "751b-51fd-10d7-f7b4", JoinParamsModel(hostname="foobar")
        )
    except NodeCantJoinError:
        throws = True
    assert throws

    throws = False
    nodemgr._init_stage = NodeInitStage.AVAILABLE
    try:
        await nodemgr.join(
            "1.2.3.4", "751b-51fd-10d7-f7b4", JoinParamsModel(hostname="")
        )
    except NodeError as e:
        throws = True
        assert "hostname" in e.message
    assert throws


@pytest.mark.asyncio
async def test_join_check_disk_solution(
    gstate: GlobalState, mocker: MockerFixture, nodemgr: NodeMgr
) -> None:

    from gravel.controllers.nodes.mgr import (
        NodeCantJoinError,
        NodeInitStage,
        JoinParamsModel,
    )
    from gravel.controllers.nodes.disks import DiskSolution

    nodemgr._init_stage = NodeInitStage.AVAILABLE

    def empty_solution(gstate: GlobalState) -> DiskSolution:
        return DiskSolution()

    mocker.patch(
        "gravel.controllers.nodes.disks.Disks.gen_solution", new=empty_solution
    )

    throws = False
    try:
        await nodemgr.join(
            "1.2.3.4", "751b-51fd-10d7-f7b4", JoinParamsModel(hostname="foobar")
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
            "1.2.3.4", "751b-51fd-10d7-f7b4", JoinParamsModel(hostname="foobar")
        )
    except AssertionError:
        throws = True
    assert throws


@pytest.mark.asyncio
async def test_join(
    gstate: GlobalState, mocker: MockerFixture, nodemgr: NodeMgr
) -> None:

    from uuid import UUID
    from gravel.controllers.nodes.mgr import NodeInitStage, JoinParamsModel
    from gravel.controllers.nodes.disks import DiskSolution, DiskModel
    from gravel.controllers.nodes.deployment import DeploymentDisksConfig

    def mock_solution(gstate: GlobalState) -> DiskSolution:
        return DiskSolution(
            systemdisk=DiskModel(path="/dev/foo", size=1000),
            storage=[
                DiskModel(path="/dev/bar", size=2000),
                DiskModel(path="/dev/baz", size=2000),
            ],
            storage_size=4000,
            possible=True,
        )

    async def mock_join(
        leader_address: str,
        token: str,
        uuid: UUID,
        hostname: str,
        address: str,
        disks: DeploymentDisksConfig,
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

    mocker.patch(
        "gravel.controllers.nodes.disks.Disks.gen_solution", new=mock_solution
    )

    nodemgr._init_stage = NodeInitStage.AVAILABLE

    nodemgr._deployment.join = mocker.AsyncMock(side_effects=Exception())
    throws = False
    try:
        await nodemgr.join(
            "10.1.2.3",
            "751b-51fd-10d7-f7b4",
            JoinParamsModel(hostname="foobar"),
        )
    except Exception:
        throws = True
    assert throws
    nodemgr._deployment.join.assert_called_once()  # type: ignore

    nodemgr._deployment.join = mocker.AsyncMock(return_value=False)
    res = await nodemgr.join(
        "10.1.2.3", "751b-51fd-10d7-f7b4", JoinParamsModel(hostname="foobar")
    )
    assert not res
    nodemgr._deployment.join.assert_called_once()  # type: ignore

    nodemgr._save_state = mocker.AsyncMock()
    nodemgr._node_start = mocker.AsyncMock()
    nodemgr._deployment.join = mock_join
    res = await nodemgr.join(
        "10.1.2.3", "751b-51fd-10d7-f7b4", JoinParamsModel(hostname="foobar")
    )
    assert res
    assert nodemgr._token == "751b-51fd-10d7-f7b4"
    nodemgr._save_state.assert_called_once()  # type: ignore
    nodemgr._node_start.assert_called_once()  # type: ignore


@pytest.mark.asyncio
async def test_deploy_checks(gstate: GlobalState, nodemgr: NodeMgr) -> None:

    from gravel.controllers.nodes.mgr import (
        NodeInitStage,
        NodeNotStartedError,
        NodeCantDeployError,
        DeployParamsModel,
    )
    from gravel.controllers.nodes.deployment import NodeStageEnum

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
        await nodemgr.deploy(DeployParamsModel(hostname="barbaz", ntpaddr=""))
    except NodeCantDeployError as e:
        assert e.message == "missing ntp server address"
        throws = True
    assert throws


@pytest.mark.asyncio
async def test_deploy_check_disk_solution(
    gstate: GlobalState, mocker: MockerFixture, nodemgr: NodeMgr
) -> None:
    from gravel.controllers.nodes.mgr import NodeInitStage, NodeCantDeployError
    from gravel.controllers.nodes.disks import DiskSolution

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
async def test_deploy(
    gstate: GlobalState, mocker: MockerFixture, nodemgr: NodeMgr
) -> None:

    from gravel.controllers.nodes.mgr import NodeInitStage
    from gravel.controllers.nodes.disks import DiskSolution, DiskModel
    from gravel.controllers.nodes.deployment import DeploymentConfig
    from gravel.controllers.auth import UserMgr, UserModel

    called_mock_deploy = False

    def mock_solution(gstate: GlobalState) -> DiskSolution:
        return DiskSolution(
            systemdisk=DiskModel(path="/dev/foo", size=1000),
            storage=[
                DiskModel(path="/dev/bar", size=2000),
                DiskModel(path="/dev/baz", size=2000),
            ],
            storage_size=4000,
            possible=True,
        )

    async def mock_deploy(
        config: DeploymentConfig,
        post_bootstrap_cb: Callable[[bool, Optional[str]], Awaitable[None]],
        finisher: Callable[[bool, Optional[str]], Awaitable[None]],
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

    nodemgr._init_stage = NodeInitStage.AVAILABLE

    nodemgr._generate_token = mocker.MagicMock(
        return_value="751b-51fd-10d7-f7b4"
    )
    nodemgr._save_token = mocker.AsyncMock()
    nodemgr._deployment.deploy = mock_deploy

    await gstate.store.ensure_connection()

    await nodemgr.deploy(
        DeployParamsModel(hostname="barbaz", ntpaddr="my.ntp.addr")
    )

    assert called_mock_deploy
    assert nodemgr._token == "751b-51fd-10d7-f7b4"
    assert nodemgr._state.hostname == "barbaz"
    nodemgr._save_token.assert_called_once()  # type: ignore

    ntpaddr = await gstate.store.get("/nodes/ntp_addr")
    assert ntpaddr == "my.ntp.addr"

    usermgr = UserMgr(gstate.store)
    assert await usermgr.exists("admin")
    user: Optional[UserModel] = await usermgr.get("admin")
    assert user is not None
    assert user.username == "admin"
    # We can't test the plain password here because it will fail
    # and we don't care particularly about the password itself, just that
    # the user has been populated. We'll leave for the 'UserMgr' tests to
    # validate the correctness of its operations.
    assert len(user.password) > 0


async def expect_assertion(coro: Awaitable[None]) -> bool:
    try:
        await coro
    except AssertionError:
        return True
    return False


@pytest.mark.asyncio
async def test_bootstrap_finisher_cb(
    gstate: GlobalState, mocker: MockerFixture, nodemgr: NodeMgr
) -> None:

    from gravel.controllers.nodes.mgr import NodeInitStage

    nodemgr._init_stage = NodeInitStage.NONE
    assert await expect_assertion(nodemgr._post_bootstrap_finisher(True, None))
    nodemgr._init_stage = NodeInitStage.PREPARE
    assert await expect_assertion(nodemgr._post_bootstrap_finisher(True, None))
    nodemgr._init_stage = NodeInitStage.STARTED
    assert await expect_assertion(nodemgr._post_bootstrap_finisher(True, None))

    nodemgr._init_stage = NodeInitStage.AVAILABLE
    nodemgr._save_state = mocker.AsyncMock()
    nodemgr._post_bootstrap_config = mocker.AsyncMock()

    await nodemgr._post_bootstrap_finisher(True, None)

    nodemgr._save_state.assert_called_once()  # type: ignore
    nodemgr._post_bootstrap_config.assert_called_once()  # type: ignore


@pytest.mark.asyncio
async def test_finish_deployment_cb(
    gstate: GlobalState, mocker: MockerFixture, nodemgr: NodeMgr
) -> None:

    from gravel.controllers.nodes.mgr import NodeInitStage

    nodemgr._init_stage = NodeInitStage.NONE
    assert await expect_assertion(nodemgr._finish_deployment(True, None))
    nodemgr._init_stage = NodeInitStage.PREPARE
    assert await expect_assertion(nodemgr._finish_deployment(True, None))
    nodemgr._init_stage = NodeInitStage.STARTED
    assert await expect_assertion(nodemgr._finish_deployment(True, None))

    nodemgr._init_stage = NodeInitStage.AVAILABLE
    nodemgr._deployment.finish_deployment = mocker.MagicMock()
    nodemgr._load = mocker.AsyncMock()
    nodemgr._node_start = mocker.AsyncMock()

    await nodemgr._finish_deployment(True, None)

    nodemgr._deployment.finish_deployment.assert_called_once()  # type: ignore
    nodemgr._load.assert_called_once()  # type: ignore
    nodemgr._node_start.assert_called_once()  # type: ignore


@pytest.mark.asyncio
async def test_postbootstrap_config(
    mocker: MockerFixture, gstate: GlobalState
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


@pytest.mark.asyncio
async def test_finish_deployment(
    gstate: GlobalState, mocker: MockerFixture, nodemgr: NodeMgr
) -> None:

    from gravel.controllers.nodes.mgr import (
        NodeAlreadyJoiningError,
        NodeNotDeployedError,
    )
    from gravel.controllers.nodes.deployment import NodeStageEnum

    orig_mark_ready = nodemgr._deployment._state.mark_ready
    nodemgr._deployment._state.mark_ready = mocker.MagicMock()
    nodemgr._deployment._state._stage = NodeStageEnum.READY
    await nodemgr.finish_deployment()

    nodemgr._deployment._state.mark_ready.assert_not_called()  # type: ignore
    nodemgr._deployment._state.mark_ready = orig_mark_ready

    nodemgr._deployment._state._stage = NodeStageEnum.JOINING
    throws = False
    try:
        await nodemgr.finish_deployment()
    except NodeAlreadyJoiningError:
        throws = True
    assert throws

    nodemgr._deployment._state._stage = NodeStageEnum.BOOTSTRAPPING
    throws = False
    try:
        await nodemgr.finish_deployment()
    except NodeNotDeployedError:
        throws = True
    assert throws

    nodemgr._deployment._state._stage = NodeStageEnum.DEPLOYED
    await nodemgr.finish_deployment()
    assert nodemgr._deployment._state._stage == NodeStageEnum.READY
    assert nodemgr.deployment_state.stage == NodeStageEnum.READY
    assert nodemgr.deployment_state.ready


def fake_conn(cb: Callable[[MessageModel], None]) -> IncomingConnection:
    class FakeConn(IncomingConnection):

        checker: Callable[[MessageModel], None]

        def __init__(self, checker: Callable[[MessageModel], None]):
            self.checker = checker

        async def send_msg(self, data: MessageModel) -> None:
            self.checker(data)

        @property
        def address(self) -> str:
            return "placeholder"

    return FakeConn(cb)


@pytest.mark.asyncio
async def test_handle_join(
    gstate: GlobalState,
    mocker: MockerFixture,
    fs: fake_filesystem.FakeFilesystem,
    nodemgr: NodeMgr,
) -> None:

    from fastapi import status
    from gravel.controllers.nodes.messages import (
        MessageModel,
        JoinMessageModel,
        ErrorMessageModel,
        WelcomeMessageModel,
        MessageTypeEnum,
    )

    nodemgr._token = "751b-51fd-10d7-f7b4"

    # test wrong token
    #
    failed_token = False

    def fail_token(data: MessageModel) -> None:
        assert data.type == MessageTypeEnum.ERROR
        msg = cast(ErrorMessageModel, data.data)
        assert msg.what == "bad token"
        assert msg.code == status.HTTP_401_UNAUTHORIZED
        nonlocal failed_token
        failed_token = True

    fail_conn = fake_conn(fail_token)
    await nodemgr._handle_join(
        fail_conn,
        JoinMessageModel(
            uuid="aaaaaaaa-d4a5-48b3-804b-99c406555c89",
            hostname="barbaz",
            address="5.6.7.8",
            token="failtoken",
        ),
    )
    assert failed_token

    # test missing address and hostname
    #
    failed_bad_addr_hostname = False

    def bad_addr_hostname(data: MessageModel) -> None:
        assert data.type == MessageTypeEnum.ERROR
        msg = cast(ErrorMessageModel, data.data)
        assert msg.what == "missing address or hostname"
        assert msg.code == status.HTTP_400_BAD_REQUEST
        nonlocal failed_bad_addr_hostname
        failed_bad_addr_hostname = True

    fail_conn = fake_conn(bad_addr_hostname)
    await nodemgr._handle_join(
        fail_conn,
        JoinMessageModel(
            uuid="aaaaaaaa-d4a5-48b3-804b-99c406555c89",
            hostname="",
            address="5.6.7.8",
            token=nodemgr._token,
        ),
    )
    assert failed_bad_addr_hostname

    failed_bad_addr_hostname = False
    fail_conn = fake_conn(bad_addr_hostname)
    await nodemgr._handle_join(
        fail_conn,
        JoinMessageModel(
            uuid="aaaaaaaa-d4a5-48b3-804b-99c406555c89",
            hostname="barbaz",
            address="",
            token=nodemgr._token,
        ),
    )
    assert failed_bad_addr_hostname

    # test add new member
    #

    class Member:
        name: str = "asd"
        peer_urls: List[str] = ["10.11.12.13"]

    called_add_member = False
    called_conn_cb = False

    async def mock_add_member(urls: List[str]) -> Tuple[Member, List[Member]]:
        nonlocal called_add_member
        called_add_member = True
        return Member(), [Member()]

    def conn_cb(data: MessageModel) -> None:
        assert data.type == MessageTypeEnum.WELCOME
        msg = WelcomeMessageModel.parse_obj(data.data)
        assert msg.pubkey == "mypubkey"
        assert msg.cephconf == "mycephconf"
        assert msg.keyring == "mycephkeyring"
        assert msg.etcd_peer == "asd=10.11.12.13"
        nonlocal called_conn_cb
        called_conn_cb = True

    mocker.patch(
        "gravel.controllers.orch.orchestrator.Orchestrator.get_public_key",
        new=mocker.MagicMock(return_value="mypubkey"),  # type: ignore
    )

    fs.create_file("/etc/ceph/ceph.conf")
    fs.create_file("/etc/ceph/ceph.client.admin.keyring")
    with open("/etc/ceph/ceph.conf", mode="w") as f:
        f.write("mycephconf")
    with open("/etc/ceph/ceph.client.admin.keyring", mode="w") as f:
        f.write("mycephkeyring")

    class FakeAETCD:
        async def add_member(
            self, urls: List[str]
        ) -> Tuple[Member, List[Member]]:
            return await mock_add_member(urls)

        async def close(self) -> None:
            pass

    mocker.patch("aetcd3.client", new=FakeAETCD)

    conn = fake_conn(conn_cb)
    await nodemgr._handle_join(
        conn,
        JoinMessageModel(
            uuid="aaaaaaaa-d4a5-48b3-804b-99c406555c89",
            hostname="barbaz",
            address="5.6.7.8",
            token=nodemgr._token,
        ),
    )
    assert called_add_member
    assert called_conn_cb
    assert "placeholder" in nodemgr._joining
    assert nodemgr._joining["placeholder"].address == "5.6.7.8"
    assert nodemgr._joining["placeholder"].hostname == "barbaz"
