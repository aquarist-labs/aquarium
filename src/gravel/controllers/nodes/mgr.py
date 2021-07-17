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
    List,
    Optional,
)
from pathlib import Path

import aetcd3
from pydantic import BaseModel, Field
from fastapi import status
from fastapi.logger import logger as fastapi_logger
from gravel.cephadm.cephadm import CephadmError
from gravel.cephadm.models import NodeInfoModel
from gravel.controllers.auth import UserModel, UserMgr
from gravel.controllers.gstate import GlobalState
from gravel.controllers.nodes.deployment import (
    DeploymentConfig,
    DeploymentDisksConfig,
    DeploymentState,
    NodeDeployment,
)
from gravel.controllers.orch.ceph import CephCommandError, Mon

from gravel.controllers.nodes.errors import (
    NodeCantJoinError,
    NodeNetworkAddressNotAvailable,
    NodeNotDeployedError,
    NodeNotStartedError,
    NodeShuttingDownError,
    NodeAlreadyJoiningError,
    NodeCantDeployError,
    NodeError,
)
from gravel.controllers.nodes.conn import (
    ConnMgr,
    get_conn_mgr,
    IncomingConnection,
)
from gravel.controllers.nodes.messages import (
    ErrorMessageModel,
    MessageModel,
    JoinMessageModel,
    ReadyToAddMessageModel,
    WelcomeMessageModel,
    MessageTypeEnum,
)
from gravel.controllers.nodes.etcd import (
    ContainerFetchError,
    etcd_pull_image,
    spawn_etcd,
)
from gravel.controllers.orch.orchestrator import (
    Orchestrator,
    OrchHostListModel,
)
from gravel.controllers.resources.inventory_sub import Subscriber
from gravel.controllers.nodes.disks import Disks
from gravel.controllers.utils import aqr_run_cmd


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


class DeployParamsBaseModel(BaseModel):
    hostname: str = Field(title="Hostname to use for this node")


class DeployParamsModel(DeployParamsBaseModel):
    ntpaddr: str = Field(title="NTP address to be used")


class JoinParamsModel(DeployParamsBaseModel):
    pass


class NodeMgr:

    _init_stage: NodeInitStage
    _connmgr: ConnMgr
    _incoming_task: asyncio.Task  # pyright: reportUnknownMemberType=false
    _shutting_down: bool
    _state: NodeStateModel
    _token: Optional[str]
    _joining: Dict[str, JoiningNodeModel]
    _deployment: NodeDeployment
    _inventory_sub: Optional[Subscriber]

    gstate: GlobalState

    def __init__(self, gstate: GlobalState):
        self._init_stage = NodeInitStage.NONE
        self._shutting_down = False
        self._connmgr = get_conn_mgr()
        self._token = None
        self._joining = {}
        self._deployment = NodeDeployment(gstate, self._connmgr)
        self._inventory_sub = None

        self.gstate = gstate

        try:
            self._init_state()
        except NodeError as e:
            raise e  # propagate

    def _init_state(self) -> None:
        # attempt reading our node state from disk; create one if not found.
        try:
            self._state = self.gstate.config.read_model("node", NodeStateModel)
        except FileNotFoundError:
            self._state = NodeStateModel(
                uuid=uuid4(), address=None, hostname=None
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
                address=self._state.address,
            )
            await self._start_ceph()
            await self._node_start()

    async def shutdown(self) -> None:
        pass

    async def _obtain_images(self) -> bool:
        cephadm = self.gstate.cephadm
        try:
            await asyncio.gather(
                cephadm.pull_images(), etcd_pull_image(self.gstate)
            )
        except ContainerFetchError as e:
            logger.error(f"unable to fetch containers: {e.message}")
            return False
        except CephadmError as e:
            logger.error(f"unable to fetch ceph containers: {str(e)}")
            return False
        return True

    async def _node_prepare(self) -> None:
        async def _inventory_subscriber(nodeinfo: NodeInfoModel) -> None:
            logger.debug(f"inventory subscriber > node info: {nodeinfo}")
            assert nodeinfo
            await self._node_update_info(nodeinfo)
            if self._init_stage == NodeInitStage.PREPARE:
                await self._node_prestart()

        async def _task() -> None:
            if not await self._obtain_images():
                # xxx: find way to shutdown here?
                return
            self._inventory_sub = await self.gstate.inventory.subscribe(
                _inventory_subscriber, once=False
            )

        self._init_stage = NodeInitStage.PREPARE
        asyncio.create_task(_task())

    async def _node_update_info(self, nodeinfo: NodeInfoModel) -> None:

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

    async def _node_prestart(self):
        """sets hostname and addresses; allows bootstrap, join."""
        assert self.deployment_state.nostage
        assert self._init_stage == NodeInitStage.PREPARE
        self._init_stage = NodeInitStage.AVAILABLE

    async def _node_start(self) -> None:
        """node is ready to accept incoming messages"""
        assert self._state
        assert self.deployment_state.ready or self.deployment_state.deployed

        logger.info("start node")

        await self._obtain_state()
        await self._load()

        self._init_stage = NodeInitStage.STARTED

        logger.info("Start connection manager")
        self._incoming_task = asyncio.create_task(self._incoming_msg_task())
        self._connmgr.start_receiving()

    async def _start_ceph(self) -> None:
        """Start ceph's systemd target"""
        ret, _, err = await aqr_run_cmd(["systemctl", "start", "ceph.target"])
        if ret:
            raise NodeError(f"Unable to start Ceph target: {err}")
        logger.info("Started ceph target")

    def _node_shutdown(self) -> None:
        """shutting down, stop node"""
        self._init_stage = NodeInitStage.STOPPING
        self._incoming_task.cancel()

    def _generate_token(self) -> str:
        def gen() -> str:
            return "".join(random.choice("0123456789abcdef") for _ in range(4))

        tokenstr = "-".join(gen() for _ in range(4))
        return tokenstr

    async def join(
        self, leader_address: str, token: str, params: JoinParamsModel
    ) -> bool:
        logger.debug(f"join > with leader {leader_address}, token: {token}")

        if self._init_stage < NodeInitStage.AVAILABLE:
            raise NodeNotStartedError()
        elif self._init_stage > NodeInitStage.AVAILABLE:
            raise NodeCantJoinError()

        if not params.hostname or len(params.hostname) == 0:
            raise NodeError("hostname parameter not provided")

        assert self._state
        assert self._state.address

        # set in-memory hostname state, write it later
        self._state.hostname = params.hostname

        disk_solution = Disks.gen_solution(self.gstate)
        if not disk_solution.possible:
            raise NodeCantJoinError("no disk deployment solution found")
        assert disk_solution.systemdisk is not None

        disks = DeploymentDisksConfig(system=disk_solution.systemdisk.path)
        disks.storage = [
            d.path for d in disk_solution.storage if d.path is not None
        ]

        try:
            res: bool = await self._deployment.join(
                leader_address,
                token,
                self._state.uuid,
                params.hostname,
                self._state.address,
                disks,
            )

            if not res:
                return False

        except Exception as e:
            # propagate exceptions
            raise e

        self._token = token
        await self._save_state()
        await self._node_start()
        return True

    async def deploy(self, params: DeployParamsModel) -> None:

        assert self._state
        if self._init_stage < NodeInitStage.AVAILABLE:
            raise NodeNotStartedError()

        if self.deployment_state.error:
            raise NodeCantDeployError("node is in error state")

        logger.debug("deploy > unsubscribe inventory updates")
        if self._inventory_sub:
            self.gstate.inventory.unsubscribe(self._inventory_sub)

        # check parameters
        if not params.ntpaddr or len(params.ntpaddr) == 0:
            raise NodeCantDeployError("missing ntp server address")
        if not params.hostname or len(params.hostname) == 0:
            raise NodeCantDeployError("missing hostname parameter")

        disk_solution = Disks.gen_solution(self.gstate)
        if not disk_solution.possible:
            raise NodeCantDeployError("no possible deployment solution found")
        assert disk_solution.systemdisk is not None

        disks = DeploymentDisksConfig(system=disk_solution.systemdisk.path)
        disks.storage = [
            d.path for d in disk_solution.storage if d.path is not None
        ]
        logger.debug(f"mgr > deploy > disks: {disks}")

        # set hostname in memory; we'll write it later
        self._state.hostname = params.hostname
        self._token = self._generate_token()
        assert self._state.address

        logger.info("deploy node")
        await self._deployment.deploy(
            DeploymentConfig(
                hostname=params.hostname,
                address=self._state.address,
                token=self._token,
                ntp_addr=params.ntpaddr,
                disks=disks,
            ),
            self._post_bootstrap_finisher,
            self._finish_deployment,
        )
        await self._save_token()
        await self._save_ntp_addr(params.ntpaddr)

        admin_user = UserModel(username="admin", password="aquarium")
        admin_user.hash_password()
        user_mgr = UserMgr(self.gstate.store)
        await user_mgr.put(admin_user)

    async def _post_bootstrap_finisher(
        self, success: bool, error: Optional[str]
    ) -> None:
        """
        Called asynchronously, presumes bootstrap was successful.
        """
        assert self._init_stage == NodeInitStage.AVAILABLE
        assert self._state
        await self._save_state()

        logger.info("finish deployment config")
        await self._post_bootstrap_config()

    async def _finish_deployment(
        self, success: bool, error: Optional[str]
    ) -> None:
        assert self._init_stage == NodeInitStage.AVAILABLE
        self._deployment.finish_deployment()

        logger.debug(f"finished deployment: token = {self._token}")
        await self._load()
        await self._node_start()

    async def _post_bootstrap_config(self) -> None:
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
            "mgr", "mgr/cephadm/manage_etc_ceph_ceph_conf", "true"
        )
        if not res:
            logger.error("unable to enable managed ceph.conf by cephadm")

        res = mon.config_set(
            "global", "auth_allow_insecure_global_id_reclaim", "false"
        )
        if not res:
            logger.error("unable to disable insecure global id reclaim")

    async def finish_deployment(self) -> None:
        assert self._state

        if self.deployment_state.ready:
            return
        elif self.deployment_state.joining:
            raise NodeAlreadyJoiningError()
        elif not self.deployment_state.deployed:
            raise NodeNotDeployedError()

        self.deployment_state.mark_ready()

    @property
    def deployment_progress(self) -> int:
        return self._deployment.progress

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

    async def _save_ntp_addr(self, ntp_addr: str) -> None:
        assert ntp_addr
        logger.info(f"saving NTP addr: {ntp_addr}")
        await self.gstate.store.put("/nodes/ntp_addr", ntp_addr)

    async def _save_state(self) -> None:
        try:
            self.gstate.config.write_model("node", self._state)
        except Exception as e:
            raise NodeError(str(e))

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
        self, conn: IncomingConnection, msg: MessageModel
    ) -> None:
        logger.debug(f"handle msg > type: {msg.type}")
        if msg.type == MessageTypeEnum.JOIN:
            logger.debug("handle msg > join")
            await self._handle_join(conn, JoinMessageModel.parse_obj(msg.data))
        elif msg.type == MessageTypeEnum.READY_TO_ADD:
            logger.debug("handle ready to add")
            await self._handle_ready_to_add(
                conn, ReadyToAddMessageModel.parse_obj(msg.data)
            )
        pass

    async def _handle_join(
        self, conn: IncomingConnection, msg: JoinMessageModel
    ) -> None:
        logger.debug(f"handle join {msg}")
        assert self._state is not None

        if msg.token != self._token:
            logger.info(f"handle join > bad token from {conn}")
            await conn.send_msg(
                MessageModel(
                    type=MessageTypeEnum.ERROR,
                    data=ErrorMessageModel(
                        what="bad token", code=status.HTTP_401_UNAUTHORIZED
                    ),
                )
            )
            return

        if not msg.address or not msg.hostname:
            logger.info(f"handle join > missing address or host from {conn}")
            await conn.send_msg(
                MessageModel(
                    type=MessageTypeEnum.ERROR,
                    data=ErrorMessageModel(
                        what="missing address or hostname",
                        code=status.HTTP_400_BAD_REQUEST,
                    ),
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

        member_urls: str = ",".join(
            [
                f"{m.name}={m.peer_urls[0]}"
                for m in nodes
                if (len(m.peer_urls) > 0 and len(m.name) > 0)
            ]
        )
        logger.debug(
            f"{member_urls=}, member: {member.name}={member.peer_urls[0]}"
        )

        welcome = WelcomeMessageModel(
            pubkey=pubkey,
            cephconf=cephconf,
            keyring=keyring,
            etcd_peer=member_urls,
        )
        try:
            logger.debug(f"handle join > send welcome: {welcome}")
            await conn.send_msg(
                MessageModel(type=MessageTypeEnum.WELCOME, data=welcome.dict())
            )
        except Exception as e:
            logger.error(f"handle join > error: {str(e)}")
            return

        logger.debug(f"handle join > welcome sent: {welcome}")
        self._joining[conn.address] = JoiningNodeModel(
            address=msg.address, hostname=msg.hostname
        )

    async def _handle_ready_to_add(
        self, conn: IncomingConnection, msg: ReadyToAddMessageModel
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
                        code=status.HTTP_428_PRECONDITION_REQUIRED,
                    ),
                )
            )
            return

        node: JoiningNodeModel = self._joining[address]
        logger.info(
            "handle ready to add > "
            f"hostname: {node.hostname}, address: {node.address}"
        )
        orch = Orchestrator(self.gstate.ceph_mgr)
        if not orch.host_add(node.hostname, node.address):
            logger.error("handle ready > failed adding host to orch")

        # reset default crush ruleset, and adjust pools to use a multi-node
        # ruleset, spreading replicas across hosts rather than osds.
        mon = self.gstate.ceph_mon
        if not mon.set_replicated_ruleset():
            logger.error(
                "handle ready to add > unable to set replicated ruleset"
            )

        await self._set_pool_default_size()

    async def _set_pool_default_size(self) -> None:
        """reset the osd pool default size"""
        assert self._init_stage == NodeInitStage.STARTED

        def get_target_size():
            orch: Orchestrator = Orchestrator(self.gstate.ceph_mgr)
            orch_hosts: List[OrchHostListModel] = orch.host_ls()
            return 2 if len(orch_hosts) < 3 else 3

        mon: Mon = self.gstate.ceph_mon
        current_size: Optional[int] = mon.get_pool_default_size()
        target_size: int = get_target_size()

        # set the default pool size
        msg = (
            "set default osd pool size >"
            f" current: {current_size}"
            f" target: {target_size}"
        )

        if current_size is None:
            logger.error(f"unable to {msg}")
            return

        logger.info(msg)
        mon.set_pool_default_size(target_size)

        # adjust the size of existing pools
        svc_pool_ids: List[int] = []  # aquarium service pool ids
        for svc in self.gstate.services.ls():
            svc_pool_ids += svc.pools

        for pool in mon.get_pools():  # all pools
            msg = (
                "set osd pool size >"
                f" pool: {pool.pool_name}"
                f" current_size: {pool.size}"
                f" target_size: {target_size}"
            )

            if pool.pool in svc_pool_ids:
                reason = "reason: pool is managed by an aquarium service"
                logger.debug(f"skipping {msg} {reason}")
                continue
            elif pool.size > target_size:
                reason = "reason: pool is user defined"
                logger.debug(f"skipping {msg} {reason}")
                continue

            logger.info(msg)
            mon.set_pool_size(pool.pool_name, target_size)
