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
import multiprocessing
from enum import Enum
from logging import Logger
from uuid import UUID, uuid4
import random
from typing import (
    Dict,
    Optional,
)
from pathlib import Path

import aetcd3
from pydantic import BaseModel
from fastapi import status
from fastapi.logger import logger as fastapi_logger
from gravel.cephadm.cephadm import CephadmError
from gravel.cephadm.models import NodeInfoModel
from gravel.controllers.gstate import GlobalState
from gravel.controllers.nodes.bootstrap import (
    BootstrapErrorEnum,
    BootstrapStage
)
from gravel.controllers.nodes.deployment import (
    DeploymentBootstrapConfig,
    DeploymentState,
    NodeDeployment
)
from gravel.controllers.orch.ceph import (
    CephCommandError,
    Mon
)

from gravel.controllers.nodes.errors import (
    NodeCantJoinError,
    NodeNetworkAddressNotAvailable,
    NodeNotBootstrappedError,
    NodeNotStartedError,
    NodeShuttingDownError,
    NodeAlreadyJoiningError,
    NodeCantBootstrapError,
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
from gravel.controllers.nodes.etcd import ContainerFetchError, etcd_pull_image, spawn_etcd
from gravel.controllers.orch.orchestrator import Orchestrator


logger: Logger = fastapi_logger


#
# INIT STATE MACHINE
# ------------------
#
# __init__() - reads / inits on-disk state    [stage: none]
#
# start()                                     [stage: none]
#     - if deployment_stage == NONE: _node_prestart()
#     - else: _node_start()
#
# _node_prepare()                            [state: none]
#     stage = PREPARE
#     obtain images
#     obtain inventory
#     _prestart()
#
# _node_prestart()                            [state: prepare]
#     populate inventory, hostname, addresses
#     stage = AVAILABLE
#
# _node_start()                               [state: none || available]
#     obtain etcd state
#     load state
#     start connmgr
#     stage = STARTED
#
# via bootstrap || join:                      [state: available]
#     _node_start()
#
# none       aquarium is running
# prestart   aquarium is prestarting, obtains images, inventory
# available  ready to be deployed
# started    has been deployed, ready to be used
#
class NodeInitStage(int, Enum):
    NONE = 0
    PREPARE = 1
    AVAILABLE = 2
    STARTED = 3
    STOPPING = 4
    STOPPED = 5


class NodeStateModel(BaseModel):
    uuid: UUID
    address: Optional[str]
    hostname: Optional[str]


class TokenModel(BaseModel):
    token: str


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
    _deployment: NodeDeployment

    gstate: GlobalState

    def __init__(self, gstate: GlobalState):
        self._init_stage = NodeInitStage.NONE
        self._shutting_down = False
        self._connmgr = get_conn_mgr()
        self._token = None
        self._joining = {}
        self._deployment = NodeDeployment(gstate, self._connmgr)

        self.gstate = gstate

        multiprocessing.set_start_method("spawn")

        # attempt reading our node state from disk; create one if not found.
        try:
            self._state = self.gstate.config.read_model("node", NodeStateModel)
        except FileNotFoundError:
            self._state = NodeStateModel(
                uuid=uuid4(),
                address=None,
                hostname=None
            )
            try:
                self.gstate.config.write_model("node", self._state)
            except Exception as e:
                raise NodeError(str(e))
        except Exception as e:
            raise NodeError(str(e))

    async def start(self) -> None:
        assert self._state
        logger.debug(f"start > {self._state}")

        if not self.deployment_state.can_start():
            raise NodeError("unable to start unstartable node")

        assert self._init_stage == NodeInitStage.NONE

        if self.deployment_state.nostage:
            await self._node_prepare()
        else:
            assert self.deployment_state.ready or self.deployment_state.deployed
            assert self._state.hostname
            assert self._state.address
            await spawn_etcd(
                self.gstate,
                new=False,
                token=None,
                hostname=self._state.hostname,
                address=self._state.address
            )
            await self._node_start()

    async def shutdown(self) -> None:
        pass

    async def _node_prepare(self) -> None:

        async def _obtain_images() -> bool:
            cephadm = self.gstate.cephadm
            try:
                await asyncio.gather(
                    cephadm.pull_images(),
                    etcd_pull_image(self.gstate)
                )
            except ContainerFetchError as e:
                logger.error(f"unable to fetch containers: {e.message}")
                return False
            except CephadmError as e:
                logger.error(f"unable to fetch ceph containers: {str(e)}")
                return False
            return True

        async def _inventory_subscriber(nodeinfo: NodeInfoModel) -> None:
            logger.debug(f"inventory subscriber > node info: {nodeinfo}")
            assert nodeinfo
            await self._node_prestart(nodeinfo)

        async def _task() -> None:
            if not await _obtain_images():
                # xxx: find way to shutdown here?
                return
            await self.gstate.inventory.subscribe(
                _inventory_subscriber,
                once=True
            )

        self._init_stage = NodeInitStage.PREPARE
        asyncio.create_task(_task())

    async def _node_prestart(self, nodeinfo: NodeInfoModel):
        """ sets hostname and addresses; allows bootstrap, join. """
        assert self.deployment_state.nostage
        assert self._init_stage == NodeInitStage.PREPARE

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
        await self._save_state()
        self._init_stage = NodeInitStage.AVAILABLE

    async def _node_start(self) -> None:
        """ node is ready to accept incoming messages, if leader """
        assert self._state
        assert self.deployment_state.ready or self.deployment_state.deployed

        logger.info("start node")

        await self._obtain_state()
        await self._load()

        self._init_stage = NodeInitStage.STARTED

        logger.info("start leader node")
        self._incoming_task = asyncio.create_task(self._incoming_msg_task())
        self._connmgr.start_receiving()

    def _node_shutdown(self) -> None:
        """ shutting down, stop node """
        self._init_stage = NodeInitStage.STOPPING
        self._incoming_task.cancel()

    def _generate_token(self) -> str:
        def gen() -> str:
            return ''.join(random.choice("0123456789abcdef") for _ in range(4))

        tokenstr = '-'.join(gen() for _ in range(4))
        return tokenstr

    async def join(self, leader_address: str, token: str) -> bool:
        logger.debug(
            f"join > with leader {leader_address}, token: {token}"
        )

        if self._init_stage < NodeInitStage.AVAILABLE:
            raise NodeNotStartedError()
        elif self._init_stage > NodeInitStage.AVAILABLE:
            raise NodeCantJoinError()

        assert self._state
        assert self._state.hostname
        assert self._state.address

        try:
            res: bool = await self._deployment.join(
                leader_address,
                token,
                self._state.uuid,
                self._state.hostname,
                self._state.address
            )

            if not res:
                return False

        except Exception as e:
            # propagate exceptions
            raise e

        self._token = token
        await self._node_start()
        return True

    async def bootstrap(self) -> None:

        assert self._state
        if self._init_stage < NodeInitStage.AVAILABLE:
            raise NodeNotStartedError()

        if self.deployment_state.error:
            raise NodeCantBootstrapError("node is in error state")

        self._token = self._generate_token()

        assert self._state.hostname
        assert self._state.address
        logger.info("bootstrap node")
        await self._deployment.bootstrap(
            DeploymentBootstrapConfig(
                hostname=self._state.hostname,
                address=self._state.address,
                token=self._token
            ),
            self._finish_bootstrap
        )
        await self._save_token()

    async def _finish_bootstrap(self, success: bool, error: Optional[str]):
        """
        Called asynchronously, presumes bootstrap was successful.
        """
        assert self._state

        logger.info("finish bootstrap config")
        await self._finish_bootstrap_config()
        self._deployment.finish_deployment()

        logger.debug(f"finished deployment: token = {self._token}")
        await self._load()
        await self._node_start()

    async def _finish_bootstrap_config(self) -> None:
        mon: Mon = self.gstate.ceph_mon
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

        res: bool = mon.set_default_ruleset()
        if not res:
            logger.error("unable to set default ruleset")

        res = mon.config_set(
            "mgr",
            "mgr/cephadm/manage_etc_ceph_ceph_conf",
            "true"
        )
        if not res:
            logger.error("unable to enable managed ceph.conf by cephadm")

    async def finish_deployment(self) -> None:
        assert self._state

        if self.deployment_state.ready:
            return
        elif self.deployment_state.joining:
            raise NodeAlreadyJoiningError()
        elif not self.deployment_state.deployed:
            raise NodeNotBootstrappedError()

        self.deployment_state.mark_ready()

    @property
    def bootstrapper_stage(self) -> BootstrapStage:
        if not self._deployment.bootstrapper:
            return BootstrapStage.NONE
        return self._deployment.bootstrapper.stage

    @property
    def bootstrapper_progress(self) -> int:
        if not self._deployment.bootstrapper:
            return 0
        return self._deployment.bootstrapper.progress

    @property
    def bootstrapper_error_code(self) -> BootstrapErrorEnum:
        if not self._deployment.bootstrapper:
            return BootstrapErrorEnum.NONE
        return self._deployment.bootstrapper.error_code

    @property
    def bootstrapper_error_msg(self) -> str:
        if not self._deployment.bootstrapper:
            return ""
        return self._deployment.bootstrapper.error_msg

    @property
    def deployment_state(self) -> DeploymentState:
        return self._deployment.state

    @property
    def inited(self) -> bool:
        return self._init_stage >= NodeInitStage.PREPARE

    @property
    def available(self) -> bool:
        return self._init_stage >= NodeInitStage.AVAILABLE

    @property
    def started(self) -> bool:
        return self._init_stage == NodeInitStage.STARTED

    @property
    def address(self) -> str:
        assert self._state
        assert self._state.address
        return self._state.address

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

    async def _obtain_state(self) -> None:

        def _watcher(key: str, value: str) -> None:
            if key == "/nodes/token":
                logger.info(f"got updated token: {value}")
                self._token = value

        self._token = await self._load_token()
        await self.gstate.store.watch("/nodes/token", _watcher)

    async def _load(self) -> None:
        self._token = await self._load_token()

    async def _load_token(self) -> Optional[str]:
        tokenstr = await self.gstate.store.get("/nodes/token")
        assert tokenstr
        return tokenstr

    async def _save_token(self) -> None:
        assert self._token
        logger.info(f"saving token: {self._token}")
        await self.gstate.store.put("/nodes/token", self._token)

    async def _save_state(self) -> None:
        try:
            self.gstate.config.write_model("node", self._state)
        except Exception as e:
            raise NodeError(str(e))

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

        orch = Orchestrator(self.gstate.ceph_mgr)
        pubkey: str = orch.get_public_key()

        cephconf_path: Path = Path("/etc/ceph/ceph.conf")
        keyring_path: Path = Path("/etc/ceph/ceph.client.admin.keyring")
        assert cephconf_path.exists()
        assert keyring_path.exists()

        cephconf: str = cephconf_path.read_text("utf-8")
        keyring: str = keyring_path.read_text("utf-8")
        assert len(cephconf) > 0
        assert len(keyring) > 0

        logger.debug(f"handle join > pubkey: {pubkey}")

        logger.debug("handle join > connect etcd client")
        etcd: aetcd3.Etcd3Client = aetcd3.client()
        peer_url: str = f"http://{msg.address}:2380"
        logger.debug(f"handle join > add '{peer_url}' to etcd")
        member, nodes = await etcd.add_member([peer_url])
        await etcd.close()
        assert member is not None
        assert nodes is not None
        assert len(nodes) > 0

        member_urls: str = ",".join([
            f"{m.name}={m.peer_urls[0]}" for m in nodes if (
                len(m.peer_urls) > 0 and len(m.name) > 0
            )
        ])
        logger.debug(f"{member_urls=}, member: {member.name}={member.peer_urls[0]}")

        welcome = WelcomeMessageModel(
            pubkey=pubkey,
            cephconf=cephconf,
            keyring=keyring,
            etcd_peer=member_urls
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
        orch = Orchestrator(self.gstate.ceph_mgr)
        if not orch.host_add(node.hostname, node.address):
            logger.error("handle ready > failed adding host to orch")

        # reset default crush ruleset, and adjust pools to use a multi-node
        # ruleset, spreading replicas across hosts rather than osds.
        mon = self.gstate.ceph_mon
        if not mon.set_replicated_ruleset():
            logger.error(
                "handle ready to add > unable to set replicated ruleset")
