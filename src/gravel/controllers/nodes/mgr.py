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
import shlex

import aetcd3
from pydantic import BaseModel
from fastapi import status
from fastapi.logger import logger as fastapi_logger
from gravel.cephadm.models import NodeInfoModel
from gravel.controllers.gstate import gstate
from gravel.controllers.nodes.bootstrap import (
    Bootstrap,
    BootstrapError,
    BootstrapErrorEnum,
    BootstrapStage
)
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
    ERROR = 5


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


# We need to rely on "spawn" because otherwise the subprocess' signal
# handler will play nasty tricks with uvicorn's and fastapi's signal
# handlers.
# For future reference,
# - uvicorn issue: https://github.com/encode/uvicorn/issues/548
# - python bug report: https://bugs.python.org/issue43064
# - somewhat of a solution, using "spawn" for multiprocessing:
# https://github.com/tiangolo/fastapi/issues/1487#issuecomment-657290725
#
# And because we need to rely on spawn, which will create a new python
# interpreter to execute what we are specifying, the function we're passing
# needs to be pickled. And nested functions, apparently, can't be pickled. Thus,
# we need to have the functions at the top-level scope.
#
def _bootstrap_etcd_process(cmd: str):

    async def _run_etcd():
        etcd_cmd = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(*etcd_cmd)
        await process.wait()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_etcd())
    except KeyboardInterrupt:
        pass


class NodeMgr:

    _init_stage: NodeInitStage
    _connmgr: ConnMgr
    _incoming_task: asyncio.Task  # pyright: reportUnknownMemberType=false
    _shutting_down: bool
    _state: NodeStateModel
    _token: Optional[str]
    _joining: Dict[str, JoiningNodeModel]
    _bootstrapper: Optional[Bootstrap]

    def __init__(self):
        self._init_stage = NodeInitStage.NONE
        self._shutting_down = False
        self._connmgr = get_conn_mgr()
        self._token = None
        self._joining = {}
        self._bootstrapper = None

        multiprocessing.set_start_method("spawn")

        self._node_init()

    async def start(self) -> None:
        assert self._state

        logger.debug(f"start > {self._state}")

        assert self._state.stage == NodeStageEnum.NONE or \
            self._state.stage == NodeStageEnum.BOOTSTRAPPED or \
            self._state.stage == NodeStageEnum.READY

        if self._state.stage == NodeStageEnum.NONE:
            await self._wait_inventory()
        else:
            assert self._state.stage == NodeStageEnum.READY or \
                self._state.stage == NodeStageEnum.BOOTSTRAPPED
            self._spawn_etcd(new=False, token=None)
            await self._node_start()

    async def shutdown(self) -> None:
        pass

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

    async def _node_prestart(self, nodeinfo: NodeInfoModel):
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
        await self._save_state()

    async def _node_start(self) -> None:
        """ node is ready to accept incoming messages, if leader """
        assert self._state
        assert self._state.stage == NodeStageEnum.READY or \
            self._state.stage == NodeStageEnum.BOOTSTRAPPED
        assert self._state.role != NodeRoleEnum.NONE

        logger.info("start node")

        await self._load()

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

    async def _wait_inventory(self) -> None:

        async def _subscriber(nodeinfo: NodeInfoModel) -> None:
            logger.debug(f"subscriber > node info: {nodeinfo}")
            assert nodeinfo
            await self._node_prestart(nodeinfo)

        get_inventory().subscribe(_subscriber, once=True)

    def _generate_token(self) -> str:
        def gen() -> str:
            return ''.join(random.choice("0123456789abcdef") for _ in range(4))

        tokenstr = '-'.join(gen() for _ in range(4))
        return tokenstr

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

        self._state.stage = NodeStageEnum.JOINING
        await self._save_state()

        reply: MessageModel = await conn.receive()
        logger.debug(f"join > recv: {reply}")
        if reply.type == MessageTypeEnum.ERROR:
            errmsg = ErrorMessageModel.parse_obj(reply.data)
            logger.error(f"join > error: {errmsg.what}")
            await conn.close()
            self._state.stage = NodeStageEnum.NONE
            await self._save_state()
            return False

        assert reply.type == MessageTypeEnum.WELCOME
        welcome = WelcomeMessageModel.parse_obj(reply.data)
        assert welcome.pubkey
        assert welcome.cephconf
        assert welcome.keyring
        assert welcome.etcd_peer

        my_url: str = \
            f"{self._state.hostname}=http://{self._state.address}:2380"
        initial_cluster: str = f"{welcome.etcd_peer},{my_url}"
        self._spawn_etcd(
            new=False,
            token=None,
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

        self._state.stage = NodeStageEnum.READY
        self._state.role = NodeRoleEnum.FOLLOWER
        await self._save_state()

        self._token = token
        await self._save_token(should_exist=False)

        await self._node_start()
        return True

    async def bootstrap(self) -> None:

        assert self._state
        if self._state.stage == NodeStageEnum.ERROR:
            raise NodeCantBootstrapError("node is in error state")

        try:
            await self._prepare_bootstrap()
        except NodeError as e:
            logger.error(f"bootstrap prepare error: {e.message}")
            raise e

        assert not self._bootstrapper
        await self._start_bootstrap()
        self._bootstrapper = Bootstrap()

        async def finish_bootstrap_cb(
            success: bool,
            error: Optional[str]
        ) -> None:
            if not success:
                error = error if error else "unknown error"
                logger.error(f"bootstrap finish error: {error}")
                await self._finish_bootstrap_error(error)
                return

            await self._finish_bootstrap()

        try:
            await self._bootstrapper.bootstrap(
                self.address, finish_bootstrap_cb
            )
        except BootstrapError as e:
            logger.error(f"bootstrap error: {e.message}")
            raise NodeCantBootstrapError(e.message)

    def _spawn_etcd(
        self,
        new: bool,
        token: Optional[str],
        initial_cluster: Optional[str] = None
    ) -> None:

        assert self._state.hostname
        assert self._state.address
        hostname = self._state.hostname
        address = self._state.address

        logger.info(f"starting etcd, hostname: {hostname}, addr: {address}")

        client_url: str = f"http://{address}:2379"
        peer_url: str = f"http://{address}:2380"

        if not initial_cluster:
            initial_cluster = f"{hostname}={peer_url}"

        args_dict: Dict[str, str] = {
            "name": hostname,
            "initial-advertise-peer-urls": peer_url,
            "listen-peer-urls": peer_url,
            "listen-client-urls": f"{client_url},http://127.0.0.1:2379",
            "advertise-client-urls": client_url,
            "initial-cluster": initial_cluster,
            "initial-cluster-state": "existing",
            "data-dir": f"/var/lib/etcd/{hostname}.etcd"
        }

        if new:
            assert token
            args_dict["initial-cluster-token"] = token
            args_dict["initial-cluster-state"] = "new"

        args = " ".join([f"--{k} {v}" for k, v in args_dict.items()])
        logger.debug(f"spawn etcd: {args}")
        etcd_cmd = f"etcd {args}"

        process = multiprocessing.Process(
            target=_bootstrap_etcd_process,
            args=(etcd_cmd,)
        )
        process.start()

    def _bootstrap_etcd(self, token: str) -> None:
        self._spawn_etcd(new=True, token=token)

    async def _prepare_bootstrap(self) -> None:
        assert self._state
        if self._state.stage == NodeStageEnum.BOOTSTRAPPING:
            raise NodeCantBootstrapError("node bootstrapping")
        elif self._state.stage > NodeStageEnum.NONE:
            raise NodeCantBootstrapError("node can't be bootstrapped")
        elif self._init_stage < NodeInitStage.PRESTART:
            raise NodeNotStartedError()

        self._token = self._generate_token()
        await self._save_token(should_exist=False)
        logger.info(f"generated new token: {self._token}")
        self._bootstrap_etcd(self._token)

    async def _start_bootstrap(self) -> None:
        assert self._state
        assert self._state.stage == NodeStageEnum.NONE
        assert self._state.hostname
        assert self._state.address
        self._state.stage = NodeStageEnum.BOOTSTRAPPING
        await self._save_state()

    async def _finish_bootstrap_error(self, error: str) -> None:
        """
        Called asynchronously, we don't benefit anyone by throwing
        exceptions, but we can easily lock down the node by setting state to
        error.
        """
        assert self._state
        assert self._state.stage == NodeStageEnum.BOOTSTRAPPING

        self._state.stage = NodeStageEnum.ERROR
        await self._save_state()

    async def _finish_bootstrap(self):
        """
        Called asynchronously, presumes bootstrap was successful.
        """
        assert self._state
        assert self._state.stage == NodeStageEnum.BOOTSTRAPPING

        logger.info("finishing bootstrap")

        await self._finish_bootstrap_config()

        self._state.stage = NodeStageEnum.BOOTSTRAPPED
        self._state.role = NodeRoleEnum.LEADER
        await self._save_state()

        logger.debug(f"finished bootstrap: token = {self._token}")

        await self._load()
        await self._node_start()

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

    @property
    def bootstrapper_stage(self) -> BootstrapStage:
        if not self._bootstrapper:
            return BootstrapStage.NONE
        return self._bootstrapper.stage

    @property
    def bootstrapper_progress(self) -> int:
        if not self._bootstrapper:
            return 0
        return self._bootstrapper.progress

    @property
    def bootstrapper_error_code(self) -> BootstrapErrorEnum:
        if not self._bootstrapper:
            return BootstrapErrorEnum.NONE
        return self._bootstrapper.error_code

    @property
    def bootstrapper_error_msg(self) -> str:
        if not self._bootstrapper:
            return ""
        return self._bootstrapper.error_msg

    async def finish_deployment(self) -> None:
        assert self._state

        if self._state.stage < NodeStageEnum.BOOTSTRAPPED:
            raise NodeNotBootstrappedError()
        elif self._state.stage == NodeStageEnum.JOINING:
            raise NodeAlreadyJoiningError()
        elif self._state.stage == NodeStageEnum.READY:
            return

        self._state.stage = NodeStageEnum.READY
        await self._save_state()

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

    async def _load(self) -> None:
        self._token = await self._load_token()

    async def _load_token(self) -> Optional[str]:
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

    async def _save_token(self, should_exist: bool = True) -> None:
        tokenfile: Path = self._get_node_file("token")

        # this check could be a single assert, but it's important to know which
        # path failed.
        if should_exist:
            assert tokenfile.exists()
        else:
            assert not tokenfile.exists()

        token: TokenModel = TokenModel(token=self._token)
        tokenfile.write_text(token.json())

    async def _save_state(self, should_exist: bool = True) -> None:
        statefile: Path = self._get_node_file("node")

        # this check could be a single assert, but it's important to know which
        # path failed.
        if should_exist:
            assert statefile.exists()
        else:
            assert not statefile.exists()

        statefile.write_text(self._state.json())

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
        member = await etcd.add_member([peer_url])
        assert member is not None

        my_url: str = \
            f"{self._state.hostname}=http://{self._state.address}:2380"
        welcome = WelcomeMessageModel(
            pubkey=pubkey,
            cephconf=cephconf,
            keyring=keyring,
            etcd_peer=my_url
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

        # reset default crush ruleset, and adjust pools to use a multi-node
        # ruleset, spreading replicas across hosts rather than osds.
        mon = Mon()
        if not mon.set_replicated_ruleset():
            logger.error(
                "handle ready to add > unable to set replicated ruleset")


_nodemgr: Optional[NodeMgr] = None


def get_node_mgr() -> NodeMgr:
    global _nodemgr
    assert _nodemgr
    return _nodemgr


async def init_node_mgr() -> None:
    global _nodemgr
    assert not _nodemgr
    logger.info("starting node manager")
    _nodemgr = NodeMgr()
    await _nodemgr.start()


async def shutdown() -> None:
    global _nodemgr
    if _nodemgr:
        logger.info("shutting down node manager")
        await _nodemgr.shutdown()
        _nodemgr = None
