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
from pathlib import Path
from typing import Awaitable, Callable, List, Optional
from uuid import UUID

from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field

from gravel.controllers.ceph.orchestrator import Orchestrator
from gravel.controllers.containers import (
    ContainerPullError,
    container_pull,
    registry_check,
    set_registry,
)
from gravel.controllers.errors import GravelError
from gravel.controllers.gstate import GlobalState
from gravel.controllers.nodes.bootstrap import Bootstrap, BootstrapError
from gravel.controllers.nodes.conn import ConnMgr
from gravel.controllers.nodes.errors import (
    NodeAlreadyJoiningError,
    NodeBootstrappingError,
    NodeCantDeployError,
    NodeCantJoinError,
    NodeChronyRestartError,
    NodeHasBeenDeployedError,
    NodeHasJoinedError,
)
from gravel.controllers.nodes.host import HostnameCtlError, set_hostname
from gravel.controllers.nodes.messages import (
    ErrorMessageModel,
    JoinMessageModel,
    MessageModel,
    MessageTypeEnum,
    ReadyToAddMessageModel,
    WelcomeMessageModel,
)
from gravel.controllers.nodes.ntp import set_ntp_addr
from gravel.controllers.nodes.systemdisk import SystemDisk
from gravel.controllers.resources.network import NetworkConfigModel

logger: Logger = fastapi_logger


class NodeStageEnum(int, Enum):
    NONE = 0
    BOOTSTRAPPING = 1
    DEPLOYED = 2
    JOINING = 3
    READY = 4
    ERROR = 5


class ProgressEnum(int, Enum):
    NONE = 0
    PREPARING = 1
    PERFORMING = 2
    ASSIMILATING = 3
    DONE = 4


class DeploymentModel(BaseModel):
    stage: NodeStageEnum = Field(NodeStageEnum.NONE)


class DeploymentDisksConfig(BaseModel):
    system: str = Field(title="Device to consume for system disk")
    storage: List[str] = Field([], title="Devices to consume for storage")


class DeploymentContainerRegistryConfig(BaseModel):
    registry: str = Field(title="Container registry location")
    insecure: bool = Field(title="Whether the container registry is insecure")


class DeploymentContainerConfig(BaseModel):
    url: str = Field(title="Container registry URL")
    secure: bool = Field(title="Container registry is secure")
    image: str = Field(title="Container image to use")


class DeploymentConfig(BaseModel):
    hostname: str
    address: str
    token: str
    ntp_addr: str
    disks: DeploymentDisksConfig
    container: Optional[DeploymentContainerConfig]
    network: Optional[NetworkConfigModel]


class DeploymentErrorEnum(int, Enum):
    NONE = 0
    CANT_BOOTSTRAP = 1
    NODE_NOT_STARTED = 2
    CANT_JOIN = 3
    CANT_ASSIMILATE = 4
    UNKNOWN_ERROR = 5


class DeploymentErrorState(BaseModel):
    code: DeploymentErrorEnum
    msg: Optional[str]


class DeploymentError(GravelError):
    pass


class SystemDiskCreationError(DeploymentError):
    pass


class DeploymentState:

    _stage: NodeStageEnum
    _gstate: GlobalState
    _error: DeploymentErrorState

    def __init__(self, gstate: GlobalState):
        self._gstate = gstate
        self._stage = NodeStageEnum.NONE
        self._error = DeploymentErrorState(
            code=DeploymentErrorEnum.NONE, msg=None
        )

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
                "deployment", DeploymentModel(stage=self._stage)
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

    @property
    def error_what(self) -> DeploymentErrorState:
        return self._error

    def can_start(self) -> bool:
        return (
            self._stage == NodeStageEnum.NONE
            or self._stage == NodeStageEnum.DEPLOYED
            or self._stage == NodeStageEnum.READY
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

    def mark_error(self, code: DeploymentErrorEnum, msg: str) -> None:
        self._stage = NodeStageEnum.ERROR
        self._error = DeploymentErrorState(code=code, msg=msg)
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
    _progress: ProgressEnum

    def __init__(self, gstate: GlobalState, connmgr: ConnMgr):
        self._gstate = gstate
        self._connmgr = connmgr
        self._state = DeploymentState(gstate)
        self._bootstrapper = None
        self._progress = ProgressEnum.NONE

    @property
    def state(self) -> DeploymentState:
        return self._state

    @property
    def bootstrapper(self) -> Optional[Bootstrap]:
        return self._bootstrapper

    @property
    def progress(self) -> int:
        if self.state.deployed:
            return 100
        elif self.state.error or self.state.nostage:
            return 0

        if not self._bootstrapper:
            return 0  # we only handle bootstrap atm

        bounds = [
            (ProgressEnum.NONE, 0, 0),
            (ProgressEnum.PREPARING, 0, 25),
            (ProgressEnum.PERFORMING, 25, 80),
            # cheat on assimilate because we don't have real progress atm.
            (ProgressEnum.ASSIMILATING, 80, 90),
            (ProgressEnum.DONE, 100, 100),
        ]
        for pname, pmin, pmax in bounds:
            if pname != self._progress:
                continue
            if pname != ProgressEnum.PERFORMING:
                return pmax  # return the max of whatever state we're in
            # we are performing the operation, which atm means bootstrapping
            delta = pmax - pmin
            bootstrap_progress = self._bootstrapper.progress
            return pmin + int((bootstrap_progress * delta) / 100)

        return 0

    async def _prepare_check(
        self,
        containerconf: Optional[DeploymentContainerConfig] = None,
    ) -> None:

        # check container image exists
        #
        ctrcfg = self._gstate.config.options.containers
        if containerconf is not None:
            assert len(containerconf.url) > 0
            assert len(containerconf.image) > 0
            ctrcfg.registry = containerconf.url
            ctrcfg.secure = containerconf.secure
            ctrcfg.image = containerconf.image

        logger.debug(f"prepare_check > registry: {ctrcfg}")
        # propagate exceptions to caller, let them handle the various errors.
        await registry_check(ctrcfg.registry, ctrcfg.image, ctrcfg.secure)

    async def _prepare_node(
        self,
        sysdiskpath: str,
        hostname: str,
        ntpaddr: Optional[str],
        network: Optional[NetworkConfigModel],
        pubkey: Optional[str],
        keyring: Optional[str],
        cephconf: Optional[str],
        is_join: bool,
        progress_cb: Optional[Callable[[int, Optional[str]], None]],
    ) -> None:
        def progress(value: int, msg: str) -> None:
            if progress_cb is not None:
                progress_cb(value, msg)

        if is_join:
            assert ntpaddr is None
            assert pubkey is not None and len(pubkey) > 0
            assert keyring is not None and len(keyring) > 0
            assert cephconf is not None and len(cephconf) > 0
        else:
            assert ntpaddr is not None and len(ntpaddr) > 0
            assert pubkey is None
            assert keyring is None
            assert cephconf is None

        def _write_keys(pubkey: str, keyring: str, conf: str) -> None:
            # write pubkey to authorized keys, allows cephadm to do stuff
            authorized_keys = Path("/root/.ssh/authorized_keys")
            authorized_keys.parent.mkdir(
                exist_ok=True, parents=True, mode=0o700
            )
            with authorized_keys.open("a") as fd:
                fd.writelines([pubkey])
                logger.debug(f"prepare_node: wrote pubkey to {authorized_keys}")

            # write ceph.conf, allows accessing the cluster
            confpath = Path("/etc/ceph/ceph.conf")
            keyringpath = Path("/etc/ceph/ceph.client.admin.keyring")
            confpath.parent.mkdir(exist_ok=True, parents=True, mode=0o755)
            confpath.write_text(conf)
            keyringpath.write_text(keyring)
            keyringpath.chmod(0o600)
            confpath.chmod(0o644)

        systemdisk = SystemDisk()
        try:
            progress(0, "Creating System Disk")
            await systemdisk.create(self._gstate, sysdiskpath)
            progress(10, "Enabling System Disk")
            await systemdisk.enable()
        except GravelError as e:
            raise SystemDiskCreationError(msg=e.message)

        if is_join:
            # We're doing a join. It should be quick. Don't track progress.
            assert (
                pubkey is not None
                and keyring is not None
                and cephconf is not None
            )
            _write_keys(pubkey, keyring, cephconf)

        if network:
            progress(15, "Applying Network Configuration")
            await self._gstate.network.apply_config(
                network.interfaces, network.nameservers, network.routes
            )

        progress(20, "Setting Hostname")
        await self._set_hostname(hostname)

        progress(30, "Setting NTP servers")
        if is_join:
            await self._gstate.store.ensure_connection()
            ntpaddr = await self._gstate.store.get("/nodes/ntp_addr")

        assert ntpaddr is not None and len(ntpaddr) > 0
        await self._set_ntp_addr(ntpaddr)

        progress(50, "Obtaining containers")
        ctrcfg = self._gstate.config.options.containers
        try:
            await set_registry(ctrcfg.registry, ctrcfg.secure)
            await container_pull(ctrcfg.registry, ctrcfg.image)
        except ContainerPullError as e:
            raise DeploymentError(msg=e.message)

        progress(100, "Finished preparing deployment")

    async def join(
        self,
        leader_address: str,
        token: str,
        uuid: UUID,
        hostname: str,
        address: str,
        disks: DeploymentDisksConfig,
        network: Optional[NetworkConfigModel],
    ) -> bool:
        logger.debug(f"join > with leader {leader_address}, token: {token}")

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
            uuid=uuid, hostname=hostname, address=address, token=token
        )
        msg = MessageModel(type=MessageTypeEnum.JOIN, data=joinmsg.dict())
        await conn.send(msg)

        reply: MessageModel = await conn.receive()
        logger.debug(f"join > recv: {reply}")
        if reply.type == MessageTypeEnum.ERROR:
            errmsg = ErrorMessageModel.parse_obj(reply.data)
            logger.error(f"join > error: {errmsg.what}")
            await conn.close()
            self._state.mark_error(
                code=DeploymentErrorEnum.CANT_JOIN, msg=errmsg.what
            )
            return False

        assert reply.type == MessageTypeEnum.WELCOME
        welcome = WelcomeMessageModel.parse_obj(reply.data)
        assert welcome.pubkey
        assert welcome.cephconf
        assert welcome.keyring

        self._state.mark_join()
        await self._prepare_node(
            disks.system,
            hostname,
            ntpaddr=None,
            network=network,
            pubkey=welcome.pubkey,
            keyring=welcome.keyring,
            cephconf=welcome.cephconf,
            is_join=True,
            progress_cb=None,
        )

        readymsg = ReadyToAddMessageModel()
        await conn.send(
            MessageModel(type=MessageTypeEnum.READY_TO_ADD, data=readymsg)
        )
        await conn.close()

        logger.debug("join > wait for host to be added")
        orch = Orchestrator(self._gstate.ceph_mgr)
        try:
            await asyncio.wait_for(orch.wait_host_added(hostname), 30.0)
        except TimeoutError:
            logger.error("join > timeout waiting for host to be added")
            raise NodeCantJoinError("Host was not added to the cluster.")
        logger.debug("join > host added, continue")

        try:
            await self._assimilate_devices(hostname, disks.storage)
        except DeploymentError as e:
            raise NodeCantJoinError(e.message)

        self._state.mark_ready()
        return True

    async def deploy(
        self,
        config: DeploymentConfig,
        post_bootstrap_cb: Callable[[bool, Optional[str]], Awaitable[None]],
        finisher: Callable[[bool, Optional[str]], Awaitable[None]],
    ) -> None:
        async def _start() -> None:
            assert self._state
            assert self._state.nostage
            self._state.mark_bootstrap()

        async def finish_bootstrap_cb(
            success: bool, error: Optional[str]
        ) -> None:
            if not success:
                logger.error(f"bootstrap finish error: {error}")
                assert self._state.bootstrapping
                if not error:
                    error = "unable to bootstrap"
                self._state.mark_error(
                    code=DeploymentErrorEnum.CANT_BOOTSTRAP, msg=error
                )
            await post_bootstrap_cb(success, error)

            try:
                orch = Orchestrator(self._gstate.ceph_mgr)
                logger.debug("deployment > wait for host to be added")
                await asyncio.wait_for(orch.wait_host_added(hostname), 30.0)
            except TimeoutError:
                logger.error("deployment > timeout wait for host to be added")
                errmsg = "node not bootstrapped until timeout expired"
                self._state.mark_error(
                    code=DeploymentErrorEnum.CANT_BOOTSTRAP, msg=errmsg
                )
                await finisher(False, errmsg)

            try:
                await _assimilate_devices()
            except DeploymentError as e:
                logger.error("unable to assimilate devices")
                logger.exception(e)
                self._state.mark_error(
                    code=DeploymentErrorEnum.CANT_ASSIMILATE, msg=e.message
                )
                await finisher(False, e.message)
            else:
                self._progress = ProgressEnum.DONE
                await finisher(True, None)

            # By now, the KV store connection thread will have well and
            # truly found the cluster and connected to it.  Still, for the
            # sake of completeness, let's give it a kick here to make it
            # explicit.
            await self._gstate.store.ensure_connection()

        async def _assimilate_devices() -> None:
            devices = config.disks.storage
            if len(devices) == 0:
                return
            logger.debug("deployment > assimilating devices")
            self._progress = ProgressEnum.ASSIMILATING
            await self._assimilate_devices(hostname, devices)
            logger.debug("deployment > devices assimilated")

        assert config.hostname
        assert config.address
        assert config.token
        assert config.ntp_addr

        hostname = config.hostname
        address = config.address

        logger.debug(f"deploy > hostname: {hostname}, addr: {address}")

        if self._state.error:
            raise NodeCantDeployError("Node is in error state.")

        try:
            await self._prepare_check(containerconf=config.container)
        except Exception:
            logger.error("Unable to start deployment: prepare checks failed.")
            raise NodeCantDeployError("failure checking node")

        self._progress = ProgressEnum.PREPARING

        await self._prepare_node(
            config.disks.system,
            config.hostname,
            config.ntp_addr,
            config.network,
            pubkey=None,
            keyring=None,
            cephconf=None,
            is_join=False,
            progress_cb=None,
        )

        assert not self._bootstrapper
        await _start()
        self._bootstrapper = Bootstrap(self._gstate)

        try:
            self._progress = ProgressEnum.PERFORMING
            await self._bootstrapper.bootstrap(address, finish_bootstrap_cb)
        except BootstrapError as e:
            logger.error(f"bootstrap error: {e.message}")
            self._state.mark_error(
                code=DeploymentErrorEnum.CANT_BOOTSTRAP, msg=e.message
            )
            raise NodeCantDeployError(e.message)

    def finish_deployment(self) -> None:
        assert self.state.bootstrapping
        logger.info("finishing deployment")
        self._state.mark_deployed()

    async def _set_ntp_addr(self, ntp_addr: str):
        try:
            await set_ntp_addr(ntp_addr)
        except NodeChronyRestartError as e:
            logger.error(f"set ntp address error: {e.message}")
            raise e

    async def _set_hostname(self, hostname: str) -> None:
        try:
            await set_hostname(hostname)
        except HostnameCtlError as e:
            logger.error(f"deploy prepare error setting hostname: {e.message}")
            raise DeploymentError(e.message)
        except Exception as e:
            logger.error(f"deploy prepare error setting hostname: {str(e)}")
            raise DeploymentError(str(e))

    async def _assimilate_devices(
        self, hostname: str, devices: List[str]
    ) -> None:
        try:
            orch = Orchestrator(self._gstate.ceph_mgr)
            if not orch.host_exists(hostname):
                raise DeploymentError("Host not part of cluster.")
            orch.assimilate_devices(hostname, devices)

            # wait a few seconds so the orchestrator settles down
            while not orch.devices_assimilated(hostname, devices):
                await asyncio.sleep(1.0)

        except Exception as e:
            raise DeploymentError(str(e))
