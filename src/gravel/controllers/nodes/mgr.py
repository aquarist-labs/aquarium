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
from uuid import UUID, uuid4
import random
from typing import (
    Dict,
    Optional,
)
from pathlib import Path

from pydantic import BaseModel
from fastapi import status
from fastapi.logger import logger as fastapi_logger
from gravel.cephadm.models import NodeInfoModel
from gravel.controllers.gstate import gstate
from gravel.controllers.orch.ceph import (
    CephCommandError,
    Mon
)
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
    ErrorMessageModel,
    MessageModel,
    JoinMessageModel,
    ReadyToAddMessageModel,
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


class TokenModel(BaseModel):
    token: str


class AquariumUUIDModel(BaseModel):
    aqarium_uuid: UUID


class JoiningNodeModel(BaseModel):
    hostname: str
    address: str


class NodeMgr:

    _init_stage: NodeInitStage
    _connmgr: ConnMgr
    _incoming_task: asyncio.Task  # pyright: reportUnknownMemberType=false
    _shutting_down: bool
    _state: NodeStateModel
    _token: Optional[str]
    _joining: Dict[str, JoiningNodeModel]

    def __init__(self):
        self._init_stage = NodeInitStage.NONE
        self._shutting_down = False
        self._connmgr = get_conn_mgr()
        self._token = None
        self._joining = {}

        self._node_init()
        assert self._state

        logger.debug(f"init > {self._state}")

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

        logger.info("start node")

        self._load()

        self._init_stage = NodeInitStage.STARTED
        if self._state.role != NodeRoleEnum.LEADER:
            return

        logger.info("start leader node")
        self._incoming_task = asyncio.create_task(self._incoming_msg_task())
        self._connmgr.start_receiving()

    def _node_shutdown(self) -> None:
        """ shutting down, stop node """
        self._init_stage = NodeInitStage.STOPPING
        self._incoming_task.cancel()

    def _wait_inventory(self) -> None:

        async def _subscriber(nodeinfo: NodeInfoModel) -> None:
            logger.debug(f"subscriber > node info: {nodeinfo}")
            assert nodeinfo
            self._node_prestart(nodeinfo)

        get_inventory().subscribe(_subscriber, once=True)

    async def join(self, leader_address: str, token: str) -> bool:
        logger.debug(
            f"join > with leader {leader_address}, token: {token}"
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
        logger.debug(f"join > conn: {conn}")

        joinmsg = JoinMessageModel(
            uuid=self._state.uuid,
            hostname=self._state.hostname,
            address=self._state.address,
            token=token
        )
        msg = MessageModel(type=MessageTypeEnum.JOIN, data=joinmsg.dict())
        await conn.send(msg)

        reply: MessageModel = await conn.receive()
        logger.debug(f"join > recv: {reply}")
        if reply.type == MessageTypeEnum.ERROR:
            errmsg = ErrorMessageModel.parse_obj(reply.data)
            logger.error(f"join > error: {errmsg.what}")
            await conn.close()
            return False

        assert reply.type == MessageTypeEnum.WELCOME
        welcome = WelcomeMessageModel.parse_obj(reply.data)
        assert welcome.pubkey

        authorized_keys: Path = Path("/root/.ssh/authorized_keys")
        if not authorized_keys.parent.exists():
            authorized_keys.parent.mkdir(0o700)
        with authorized_keys.open("a") as fd:
            fd.writelines([welcome.pubkey])
            logger.debug(f"join > wrote pubkey to {authorized_keys}")

        readymsg = ReadyToAddMessageModel()
        await conn.send(
            MessageModel(
                type=MessageTypeEnum.READY_TO_ADD,
                data=readymsg
            )
        )
        await conn.close()
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

        await self._finish_bootstrap_config()

        tokenfile: Path = self._get_node_file("token")
        statefile: Path = self._get_node_file("node")

        assert not tokenfile.exists()
        assert statefile.exists()

        self._state.stage = NodeStageEnum.BOOTSTRAPPED
        self._state.role = NodeRoleEnum.LEADER
        statefile.write_text(self._state.json())

        def gen() -> str:
            return ''.join(random.choice("0123456789abcdef") for _ in range(4))

        tokenstr = '-'.join(gen() for _ in range(4))
        token: TokenModel = TokenModel(token=tokenstr)
        tokenfile.write_text(token.json())

        self._load()
        self._node_start()

    async def _finish_bootstrap_config(self) -> None:
        mon: Mon = Mon()
        try:
            mon.set_allow_pool_size_one()
        except CephCommandError as e:
            logger.error("unable to allow pool size 1")
            logger.debug(str(e))

        try:
            mon.disable_warn_on_no_redundancy()
        except CephCommandError as e:
            logger.error("unable to disable redundancy warning")
            logger.debug(str(e))

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
    def inited(self) -> bool:
        return self._init_stage >= NodeInitStage.PRESTART

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
            tokenfile: Path = self._get_node_file("token")
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
        self._token = self._load_token()

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

    def _get_hostname(self) -> str:
        return ""

    def _get_address(self) -> str:
        return ""

    async def _incoming_msg_task(self) -> None:
        logger.info("start handling incoming messages")
        while not self._shutting_down:
            logger.debug("incoming msg task > wait")
            conn, msg = await self._connmgr.wait_incoming_msg()
            logger.debug(f"incoming msg task > {conn}, {msg}")
            await self._handle_incoming_msg(conn, msg)
            logger.debug("incoming msg task > handled")

        logger.info("stop handling incoming messages")

    async def _handle_incoming_msg(
        self,
        conn: IncomingConnection,
        msg: MessageModel
    ) -> None:
        logger.debug(f"handle msg > type: {msg.type}")
        if msg.type == MessageTypeEnum.JOIN:
            logger.debug("handle msg > join")
            await self._handle_join(conn, JoinMessageModel.parse_obj(msg.data))
        elif msg.type == MessageTypeEnum.READY_TO_ADD:
            logger.debug("handle ready to add")
            await self._handle_ready_to_add(
                conn,
                ReadyToAddMessageModel.parse_obj(msg.data)
            )
        pass

    async def _handle_join(
        self,
        conn: IncomingConnection,
        msg: JoinMessageModel
    ) -> None:
        logger.debug(f"handle join {msg}")
        assert self._state is not None

        if msg.token != self._token:
            logger.info(f"handle join > bad token from {conn}")
            await conn.send_msg(
                MessageModel(
                    type=MessageTypeEnum.ERROR,
                    data=ErrorMessageModel(
                        what="bad token",
                        code=status.HTTP_401_UNAUTHORIZED
                    )
                )
            )
            return

        if not msg.address or not msg.hostname:
            logger.info(
                f"handle join > missing address or host from {conn}"
            )
            await conn.send_msg(
                MessageModel(
                    type=MessageTypeEnum.ERROR,
                    data=ErrorMessageModel(
                        what="missing address or hostname",
                        code=status.HTTP_400_BAD_REQUEST
                    )
                )
            )
            return

        orch = Orchestrator()
        pubkey: str = orch.get_public_key()

        logger.debug(f"handle join > pubkey: {pubkey}")

        welcome = WelcomeMessageModel(
            pubkey=pubkey
        )
        try:
            logger.debug(f"handle join > send welcome: {welcome}")
            await conn.send_msg(
                MessageModel(
                    type=MessageTypeEnum.WELCOME,
                    data=welcome.dict()
                )
            )
        except Exception as e:
            logger.error(f"handle join > error: {str(e)}")
            return

        logger.debug(f"handle join > welcome sent: {welcome}")
        self._joining[conn.address] = \
            JoiningNodeModel(address=msg.address, hostname=msg.hostname)

    async def _handle_ready_to_add(
        self,
        conn: IncomingConnection,
        msg: ReadyToAddMessageModel
    ) -> None:
        logger.debug(f"handle ready to add from {conn}")
        address: str = conn.address

        if address not in self._joining:
            logger.info(f"handle ready to add > unknown node {conn}")
            await conn.send_msg(
                MessageModel(
                    type=MessageTypeEnum.ERROR,
                    data=ErrorMessageModel(
                        what="node not joining",
                        code=status.HTTP_428_PRECONDITION_REQUIRED
                    )
                )
            )
            return

        node: JoiningNodeModel = self._joining[address]
        logger.info("handle ready to add > "
                    f"hostname: {node.hostname}, address: {node.address}")
        orch = Orchestrator()
        if not orch.host_add(node.hostname, node.address):
            logger.error("handle ready > failed adding host to orch")


_nodemgr: Optional[NodeMgr] = None


def get_node_mgr() -> NodeMgr:
    global _nodemgr
    assert _nodemgr
    return _nodemgr


def init_node_mgr() -> None:
    global _nodemgr
    assert not _nodemgr
    _nodemgr = NodeMgr()
