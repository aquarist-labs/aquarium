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


from enum import Enum
from logging import Logger
from pathlib import Path
from typing import (
    Awaitable,
    Callable,
    Optional
)
from uuid import UUID
from pydantic import BaseModel, Field
from fastapi.logger import logger as fastapi_logger

from gravel.controllers.errors import GravelError
from gravel.controllers.gstate import GlobalState
from gravel.controllers.nodes.bootstrap import (
    Bootstrap,
    BootstrapError
)
from gravel.controllers.nodes.conn import ConnMgr

from gravel.controllers.nodes.errors import (
    NodeAlreadyJoiningError,
    NodeBootstrappingError,
    NodeCantBootstrapError,
    NodeError,
    NodeHasBeenDeployedError,
    NodeHasJoinedError
)
from gravel.controllers.nodes.messages import (
    ErrorMessageModel,
    JoinMessageModel,
    MessageModel,
    MessageTypeEnum,
    ReadyToAddMessageModel,
    WelcomeMessageModel
)
from gravel.controllers.nodes.etcd import spawn_etcd


logger: Logger = fastapi_logger


class NodeStageEnum(int, Enum):
    NONE = 0
    BOOTSTRAPPING = 1
    DEPLOYED = 2
    JOINING = 3
    READY = 4
    ERROR = 5


class DeploymentModel(BaseModel):
    stage: NodeStageEnum = Field(NodeStageEnum.NONE)


class DeploymentBootstrapConfig(BaseModel):
    hostname: str
    address: str
    token: str


class DeploymentError(GravelError):
    pass


class DeploymentState:

    _stage: NodeStageEnum
    _gstate: GlobalState

    def __init__(self, gstate: GlobalState):
        self._gstate = gstate
        self._stage = NodeStageEnum.NONE

        self._load_stage()

        pass

    def _load_stage(self) -> None:
        try:
            dep = self._gstate.config.read_model("deployment", DeploymentModel)
            self._stage = dep.stage
        except FileNotFoundError:
            self._gstate.config.write_model("deployment", DeploymentModel())

    def _save_stage(self) -> None:
        try:
            self._gstate.config.write_model(
                "deployment",
                DeploymentModel(stage=self._stage)
            )
        except Exception as e:
            raise DeploymentError(str(e))

    @property
    def stage(self) -> NodeStageEnum:
        return self._stage

    @property
    def nostage(self) -> bool:
        return self._stage == NodeStageEnum.NONE

    @property
    def bootstrapping(self) -> bool:
        return self._stage == NodeStageEnum.BOOTSTRAPPING

    @property
    def joining(self) -> bool:
        return self._stage == NodeStageEnum.JOINING

    @property
    def deployed(self) -> bool:
        return self._stage == NodeStageEnum.DEPLOYED

    @property
    def ready(self) -> bool:
        return self._stage == NodeStageEnum.READY

    @property
    def error(self) -> bool:
        return self._stage == NodeStageEnum.ERROR

    def can_start(self) -> bool:
        return (
            self._stage == NodeStageEnum.NONE or
            self._stage == NodeStageEnum.DEPLOYED or
            self._stage == NodeStageEnum.READY
        )

    def mark_bootstrap(self) -> None:
        assert self.nostage
        self._stage = NodeStageEnum.BOOTSTRAPPING
        self._save_stage()

    def mark_join(self) -> None:
        assert not self.joining
        assert not self.error
        self._stage = NodeStageEnum.JOINING
        self._save_stage()

    def mark_deployed(self) -> None:
        assert not self.error
        self._stage = NodeStageEnum.DEPLOYED
        self._save_stage()

    def mark_error(self) -> None:
        self._stage = NodeStageEnum.ERROR
        self._save_stage()

    def mark_ready(self) -> None:
        assert not self.error
        self._stage = NodeStageEnum.READY
        self._save_stage()


class NodeDeployment:

    _state: DeploymentState
    _gstate: GlobalState
    _connmgr: ConnMgr
    _bootstrapper: Optional[Bootstrap]

    def __init__(
        self,
        gstate: GlobalState,
        connmgr: ConnMgr
    ):
        self._gstate = gstate
        self._connmgr = connmgr
        self._state = DeploymentState(gstate)
        self._bootstrapper = None

    @property
    def state(self) -> DeploymentState:
        return self._state

    @property
    def bootstrapper(self) -> Optional[Bootstrap]:
        return self._bootstrapper

    async def join(
        self,
        leader_address: str,
        token: str,
        uuid: UUID,
        hostname: str,
        address: str
    ) -> bool:
        logger.debug(
            f"join > with leader {leader_address}, token: {token}"
        )

        assert self._state
        assert hostname
        assert address

        if self._state.bootstrapping:
            raise NodeBootstrappingError()
        elif self._state.deployed:
            raise NodeHasBeenDeployedError()
        elif self._state.joining:
            raise NodeAlreadyJoiningError()
        elif self._state.ready:
            raise NodeHasJoinedError()
        assert self._state.nostage

        uri: str = f"ws://{leader_address}/api/nodes/ws"
        conn = await self._connmgr.connect(uri)
        logger.debug(f"join > conn: {conn}")

        joinmsg = JoinMessageModel(
            uuid=uuid,
            hostname=hostname,
            address=address,
            token=token
        )
        msg = MessageModel(type=MessageTypeEnum.JOIN, data=joinmsg.dict())
        await conn.send(msg)

        self._state.mark_join()

        reply: MessageModel = await conn.receive()
        logger.debug(f"join > recv: {reply}")
        if reply.type == MessageTypeEnum.ERROR:
            errmsg = ErrorMessageModel.parse_obj(reply.data)
            logger.error(f"join > error: {errmsg.what}")
            await conn.close()
            self._state.mark_error()
            return False

        assert reply.type == MessageTypeEnum.WELCOME
        welcome = WelcomeMessageModel.parse_obj(reply.data)
        assert welcome.pubkey
        assert welcome.cephconf
        assert welcome.keyring
        assert welcome.etcd_peer

        my_url: str = \
            f"{hostname}=http://{address}:2380"
        initial_cluster: str = f"{welcome.etcd_peer},{my_url}"
        await spawn_etcd(
            self._gstate,
            new=False,
            token=None,
            hostname=hostname,
            address=address,
            initial_cluster=initial_cluster
        )

        authorized_keys: Path = Path("/root/.ssh/authorized_keys")
        if not authorized_keys.parent.exists():
            authorized_keys.parent.mkdir(0o700)
        with authorized_keys.open("a") as fd:
            fd.writelines([welcome.pubkey])
            logger.debug(f"join > wrote pubkey to {authorized_keys}")

        cephconf_path: Path = Path("/etc/ceph/ceph.conf")
        keyring_path: Path = Path("/etc/ceph/ceph.client.admin.keyring")
        if not cephconf_path.parent.exists():
            cephconf_path.parent.mkdir(0o755)
        cephconf_path.write_text(welcome.cephconf)
        keyring_path.write_text(welcome.keyring)
        keyring_path.chmod(0o600)
        cephconf_path.chmod(0o644)

        readymsg = ReadyToAddMessageModel()
        await conn.send(
            MessageModel(
                type=MessageTypeEnum.READY_TO_ADD,
                data=readymsg
            )
        )
        await conn.close()

        self._state.mark_ready()
        return True

    async def _prepare_etcd(
        self,
        hostname: str,
        address: str,
        token: str
    ) -> None:
        assert self._state
        if self._state.bootstrapping:
            raise NodeCantBootstrapError("node bootstrapping")
        elif not self._state.nostage:
            raise NodeCantBootstrapError("node can't be bootstrapped")

        await spawn_etcd(
            self._gstate,
            new=True,
            token=token,
            hostname=hostname,
            address=address
        )

    async def bootstrap(
        self,
        config: DeploymentBootstrapConfig,
        finisher: Callable[[bool, Optional[str]], Awaitable[None]]
    ) -> None:

        assert config.hostname
        assert config.address
        assert config.token

        hostname = config.hostname
        address = config.address
        token = config.token

        if self._state.error:
            raise NodeCantBootstrapError("node is in error state")

        async def _start() -> None:
            assert self._state
            assert self._state.nostage
            self._state.mark_bootstrap()

        async def finish_bootstrap_cb(
            success: bool,
            error: Optional[str]
        ) -> None:
            if not success:
                logger.error(f"bootstrap finish error: {error}")
                assert self._state.bootstrapping
                self._state.mark_error()
            await finisher(success, error)

        try:
            await self._prepare_etcd(hostname, address, token)
        except NodeError as e:
            logger.error(f"bootstrap prepare error: {e.message}")
            raise e

        assert not self._bootstrapper
        await _start()
        self._bootstrapper = Bootstrap(self._gstate)

        try:
            await self._bootstrapper.bootstrap(
                address, finish_bootstrap_cb
            )
        except BootstrapError as e:
            logger.error(f"bootstrap error: {e.message}")
            raise NodeCantBootstrapError(e.message)

    def finish_deployment(self) -> None:
        assert self.state.bootstrapping
        logger.info("finishing bootstrap")
        self._state.mark_deployed()
