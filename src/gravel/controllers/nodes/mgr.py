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
from logging import Logger
from datetime import datetime as dt
from uuid import UUID, uuid4
import random
from typing import (
    Optional,
    List
)
from pathlib import Path

from pydantic import BaseModel
from fastapi.logger import logger as fastapi_logger
from gravel.cephadm.models import NodeInfoModel
from gravel.controllers.gstate import gstate
from gravel.controllers.resources.inventory import get_inventory

from gravel.controllers.nodes.errors import (
    NodeCantJoinError,
    NodeNetworkAddressNotAvailable,
    NodeNotBootstrappedError,
    NodeNotStartedError,
    NodeShuttingDownError,
    NodeBootstrappingError,
    NodeHasBeenDeployedError,
    NodeAlreadyJoiningError,
    NodeCantBootstrapError,
    NodeHasJoinedError,
    NodeError
)
from gravel.controllers.nodes.conn import (
    ConnMgr,
    get_conn_mgr,
    IncomingConnection
)
from gravel.controllers.nodes.messages import (
    MessageModel,
    JoinMessageModel,
    WelcomeMessageModel,
    MessageTypeEnum,
)
from gravel.controllers.orch.orchestrator import Orchestrator


logger: Logger = fastapi_logger


class NodeRoleEnum(int, Enum):
    NONE = 0
    LEADER = 1
    FOLLOWER = 2


class NodeStageEnum(int, Enum):
    NONE = 0
    BOOTSTRAPPING = 1
    BOOTSTRAPPED = 2
    JOINING = 3
    READY = 4


class NodeInitStage(int, Enum):
    NONE = 0
    PRESTART = 1
    STARTED = 2
    STOPPING = 3
    STOPPED = 4


class NodeStateModel(BaseModel):
    uuid: UUID
    role: NodeRoleEnum
    stage: NodeStageEnum
    address: Optional[str]
    hostname: Optional[str]


class ManifestModel(BaseModel):
    aquarium_uuid: UUID
    version: int
    modified: dt
    nodes: List[NodeStateModel]


class TokenModel(BaseModel):
    token: str


class AquariumUUIDModel(BaseModel):
    aqarium_uuid: UUID


class NodeMgr:

    _init_stage: NodeInitStage
    _connmgr: ConnMgr
    _incoming_task: asyncio.Task  # pyright: reportUnknownMemberType=false
    _shutting_down: bool
    _state: NodeStateModel
    _manifest: Optional[ManifestModel]
    _token: Optional[str]
    _aquarium_uuid: Optional[UUID]

    def __init__(self):
        self._init_stage = NodeInitStage.NONE
        self._shutting_down = False
        self._connmgr = get_conn_mgr()
        self._manifest = None
        self._token = None
        self._aquarium_uuid = None

        self._node_init()
        assert self._state

        logger.debug(f"=> mgr -- init > {self._state}")

        assert self._state.stage == NodeStageEnum.NONE or \
               self._state.stage == NodeStageEnum.BOOTSTRAPPED or \
               self._state.stage == NodeStageEnum.READY

        if self._state.stage == NodeStageEnum.NONE:
            self._wait_inventory()
        else:
            assert self._state.stage == NodeStageEnum.READY or \
                   self._state.stage == NodeStageEnum.BOOTSTRAPPED
            self._node_start()

    def _node_prestart(self, nodeinfo: NodeInfoModel):
        """ sets hostname and addresses; allows bootstrap, join. """
        assert self._state.stage == NodeStageEnum.NONE
        assert self._init_stage == NodeInitStage.NONE

        self._init_stage = NodeInitStage.PRESTART
        self._state.hostname = nodeinfo.hostname

        address: Optional[str] = None
        for nic in nodeinfo.nics.values():
            if nic.iftype == "loopback":
                continue
            address = nic.ipv4_address
            break

        if not address:
            raise NodeNetworkAddressNotAvailable()

        assert address
        netmask_idx = address.find("/")
        if netmask_idx > 0:
            address = address[:netmask_idx]

        self._state.address = address

        statefile: Path = self._get_node_file("node")
        assert statefile.exists()
        statefile.write_text(self._state.json())

    def _node_start(self) -> None:
        """ node is ready to accept incoming messages, if leader """
        assert self._state
        assert self._state.stage == NodeStageEnum.READY or \
               self._state.stage == NodeStageEnum.BOOTSTRAPPED
        assert self._state.role != NodeRoleEnum.NONE

        logger.info("=> mgr -- start node")

        self._init_stage = NodeInitStage.STARTED
        if self._state.role != NodeRoleEnum.LEADER:
            return

        logger.info("=> mgr -- start leader node")
        self._incoming_task = asyncio.create_task(self._incoming_msg_task())
        self._connmgr.start_receiving()

    def _node_shutdown(self) -> None:
        """ shutting down, stop node """
        self._init_stage = NodeInitStage.STOPPING
        self._incoming_task.cancel()

    def _wait_inventory(self) -> None:

        async def _subscriber(nodeinfo: NodeInfoModel) -> None:
            logger.debug(f"=> mgr -- subscriber > node info: {nodeinfo}")
            assert nodeinfo
            self._node_prestart(nodeinfo)

        get_inventory().subscribe(_subscriber, once=True)

    async def join(self, leader_address: str, token: str) -> bool:
        logger.debug(
            f"=> mgr -- join > with leader {leader_address}, token: {token}"
        )

        if self._init_stage == NodeInitStage.NONE:
            raise NodeNotStartedError()
        elif self._init_stage > NodeInitStage.PRESTART:
            raise NodeCantJoinError()

        assert self._state
        assert self._state.hostname
        assert self._state.address

        if self._state.stage == NodeStageEnum.BOOTSTRAPPING:
            raise NodeBootstrappingError()
        elif self._state.stage == NodeStageEnum.BOOTSTRAPPED:
            raise NodeHasBeenDeployedError()
        elif self._state.stage == NodeStageEnum.JOINING:
            raise NodeAlreadyJoiningError()
        elif self._state.stage == NodeStageEnum.READY:
            raise NodeHasJoinedError()
        assert self._state.stage == NodeStageEnum.NONE
        assert self._state.role == NodeRoleEnum.NONE

        uri: str = f"ws://{leader_address}/api/nodes/ws"
        conn = await self._connmgr.connect(uri)
        logger.debug(f"=> mgr -- join > conn: {conn}")

        joinmsg = JoinMessageModel(
            uuid=self._state.uuid,
            hostname=self._state.hostname,
            address=self._state.address,
            token=token
        )
        msg = MessageModel(type=MessageTypeEnum.JOIN, data=joinmsg.dict())
        await conn.send(msg)

        reply: MessageModel = await conn.receive()
        logger.debug(f"=> mgr -- join > recv: {reply}")
        assert reply.type == MessageTypeEnum.WELCOME
        welcome = WelcomeMessageModel.parse_obj(reply.data)
        assert welcome.aquarium_uuid
        assert welcome.pubkey

        authorized_keys: Path = Path("/root/.ssh/authorized_keys")
        if not authorized_keys.parent.exists():
            authorized_keys.parent.mkdir(0o700)
        with authorized_keys.open("a") as fd:
            fd.writelines([welcome.pubkey])
            logger.debug(f"=> mgr -- join > wrote pubkey to {authorized_keys}")

        self._write_aquarium_uuid(welcome.aquarium_uuid)

        return True

    async def prepare_bootstrap(self) -> None:
        assert self._state
        if self._state.stage > NodeStageEnum.NONE:
            raise NodeCantBootstrapError()
        elif self._init_stage < NodeInitStage.PRESTART:
            raise NodeNotStartedError()

    async def start_bootstrap(self) -> None:
        assert self._state
        assert self._state.stage == NodeStageEnum.NONE
        assert self._state.hostname
        assert self._state.address
        self._state.stage = NodeStageEnum.BOOTSTRAPPING

        statefile: Path = self._get_node_file("node")
        statefile.write_text(self._state.json())

    async def finish_bootstrap(self):
        assert self._state
        assert self._state.stage == NodeStageEnum.BOOTSTRAPPING
        manifestfile: Path = self._get_node_file("manifest")
        tokenfile: Path = self._get_node_file("token")
        statefile: Path = self._get_node_file("node")

        assert not manifestfile.exists()
        assert not tokenfile.exists()
        assert statefile.exists()

        self._state.stage = NodeStageEnum.BOOTSTRAPPED
        self._state.role = NodeRoleEnum.LEADER
        statefile.write_text(self._state.json())

        manifest: ManifestModel = ManifestModel(
            aquarium_uuid=uuid4(),
            version=1,
            modified=dt.now(),
            nodes=[self._state]
        )
        manifestfile.write_text(manifest.json())

        def gen() -> str:
            return ''.join(random.choice("0123456789abcdef") for _ in range(4))

        tokenstr = '-'.join(gen() for _ in range(4))
        token: TokenModel = TokenModel(token=tokenstr)
        tokenfile.write_text(token.json())

        self._load()

    async def finish_deployment(self) -> None:
        assert self._state

        if self._state.stage < NodeStageEnum.BOOTSTRAPPED:
            raise NodeNotBootstrappedError()
        elif self._state.stage == NodeStageEnum.JOINING:
            raise NodeAlreadyJoiningError()
        elif self._state.stage == NodeStageEnum.READY:
            return

        self._state.stage = NodeStageEnum.READY
        statefile: Path = self._get_node_file("node")
        assert statefile.exists()
        statefile.write_text(self._state.json())

    @property
    def stage(self) -> NodeStageEnum:
        assert self._state
        return self._state.stage

    @property
    def address(self) -> str:
        assert self._state
        assert self._state.address
        return self._state.address

    @property
    def bootstrapping(self) -> bool:
        if not self._state:
            return False
        return self._state.stage == NodeStageEnum.BOOTSTRAPPING

    @property
    def bootstrapped(self) -> bool:
        if not self._state:
            return False
        return self._state.stage == NodeStageEnum.BOOTSTRAPPED

    @property
    def ready(self) -> bool:
        if not self._state:
            return False
        return self._state.stage == NodeStageEnum.READY

    @property
    def connmgr(self) -> ConnMgr:
        if not self._connmgr:
            raise NodeNotStartedError()
        elif self._shutting_down:
            raise NodeShuttingDownError()
        return self._connmgr

    @property
    def token(self) -> Optional[str]:
        return self._token

    def _get_node_file(self, what: str) -> Path:
        confdir: Path = gstate.config.confdir
        assert confdir.exists()
        assert confdir.is_dir()
        return confdir.joinpath(f"{what}.json")

    def _node_init(self) -> None:
        statefile: Path = self._get_node_file("node")
        if not statefile.exists():
            # other control files must not exist either
            manifestfile: Path = self._get_node_file("manifest")
            tokenfile: Path = self._get_node_file("token")
            assert not manifestfile.exists()
            assert not tokenfile.exists()

            state = NodeStateModel(
                uuid=uuid4(),
                role=NodeRoleEnum.NONE,
                stage=NodeStageEnum.NONE,
                address=None,
                hostname=None
            )
            try:
                statefile.write_text(state.json())
            except Exception as e:
                raise NodeError(str(e))
            assert statefile.exists()

        self._state = NodeStateModel.parse_file(statefile)

    def _load(self) -> None:
        self._manifest = self._load_manifest()
        self._token = self._load_token()
        self._aquarium_uuid = self._load_aquarium_uuid()

        assert (self._state and self._manifest) or \
               (not self._state and not self._manifest)

    def _load_manifest(self) -> Optional[ManifestModel]:
        assert self._state
        confdir: Path = gstate.config.confdir
        assert confdir.exists()
        assert confdir.is_dir()
        manifestfile: Path = confdir.joinpath("manifest.json")
        if not manifestfile.exists():
            assert self._state.stage < NodeStageEnum.BOOTSTRAPPED
            return None
        return ManifestModel.parse_file(manifestfile)

    def _load_token(self) -> Optional[str]:
        assert self._state
        confdir: Path = gstate.config.confdir
        assert confdir.exists()
        assert confdir.is_dir()
        tokenfile: Path = confdir.joinpath("token.json")
        if not tokenfile.exists():
            assert self._state.stage < NodeStageEnum.BOOTSTRAPPED
            return None
        token = TokenModel.parse_file(tokenfile)
        return token.token

    def _load_aquarium_uuid(self) -> Optional[UUID]:
        assert self._state
        confdir: Path = gstate.config.confdir
        assert confdir.exists()
        assert confdir.is_dir()
        uuidfile: Path = confdir.joinpath("aquarium_uuid.json")
        if not uuidfile.exists():
            assert self._state.stage < NodeStageEnum.READY
            return None
        uuid = AquariumUUIDModel.parse_file(uuidfile)
        return uuid.aqarium_uuid

    def _write_aquarium_uuid(self, uuid: UUID) -> None:
        pass

    def _get_hostname(self) -> str:
        return ""

    def _get_address(self) -> str:
        return ""

    async def _incoming_msg_task(self) -> None:
        logger.info("=> mgr -- start handling incoming messages")
        while not self._shutting_down:
            logger.debug("=> mgr -- incoming msg task > wait")
            conn, msg = await self._connmgr.wait_incoming_msg()
            logger.debug(f"=> mgr -- incoming msg task > {conn}, {msg}")
            await self._handle_incoming_msg(conn, msg)
            logger.debug("=> mgr -- incoming msg task > handled")

        logger.info("=> mgr -- stop handling incoming messages")

    async def _handle_incoming_msg(
        self,
        conn: IncomingConnection,
        msg: MessageModel
    ) -> None:
        logger.debug(f"=> mgr -- handle msg > type: {msg.type}")
        if msg.type == MessageTypeEnum.JOIN:
            logger.debug("=> mgr -- handle msg > join")
            await self._handle_join(conn, JoinMessageModel.parse_obj(msg.data))
        pass

    async def _handle_join(
        self,
        conn: IncomingConnection,
        msg: JoinMessageModel
    ) -> None:
        logger.debug(f"=> mgr -- handle join {msg}")
        assert self._state is not None

        orch = Orchestrator()
        pubkey: str = orch.get_public_key()

        welcome = WelcomeMessageModel(
            cluster_uuid=self._state.uuid,
            pubkey=pubkey
        )
        try:
            await conn.send_msg(
                MessageModel(
                    type=MessageTypeEnum.WELCOME,
                    data=welcome.dict()
                )
            )
        except Exception as e:
            logger.error(f"=> mgr -- handle join > error: {str(e)}")
        logger.debug(f"=> mgr -- handle join > welcome sent: {welcome}")


_nodemgr: Optional[NodeMgr] = None


def get_node_mgr() -> NodeMgr:
    global _nodemgr
    assert _nodemgr
    return _nodemgr


def init_node_mgr() -> None:
    global _nodemgr
    assert not _nodemgr
    _nodemgr = NodeMgr()
