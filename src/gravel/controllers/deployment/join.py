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

# pyright: reportUnknownMemberType=false

"""
Controls the joining procedure from both ends: the node wanting to join the
cluster, and the node handling the join request.

This happens only after a node has been installed.
"""

import asyncio
from datetime import datetime as dt
from enum import Enum
from logging import Logger
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

import requests
from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field
from pydantic.error_wrappers import ValidationError
from gravel.controllers.ceph.ceph import CephCommandError
from gravel.controllers.ceph.models import OrchHostListModel

from gravel.controllers.ceph.orchestrator import Orchestrator, UnknownHostError
from gravel.controllers.config import ContainersOptionsModel
from gravel.controllers.containers import (
    ContainerError,
    ContainerPullError,
    container_pull,
    set_registry,
)
from gravel.controllers.errors import GravelError
from gravel.controllers.gstate import GlobalState
from gravel.controllers.kv import KV
from gravel.controllers.nodes.errors import NodeChronyRestartError
from gravel.controllers.nodes.host import HostnameCtlError, set_hostname
from gravel.controllers.nodes.mgr import NodeMgr
from gravel.controllers.nodes.ntp import set_ntp_addr


logger: Logger = fastapi_logger


class JoinError(GravelError):
    pass


class AlreadyJoiningError(JoinError):
    pass


class AlreadyJoinedError(JoinError):
    pass


class NotJoiningError(JoinError):
    pass


class BadTokenError(JoinError):
    pass


class HostnameExistsError(JoinError):
    pass


class JoinProgress(BaseModel):
    joined: bool = Field(False, title="Node has joined the cluster.")
    progress: int = Field(0, title="Join progress percent.")
    msg: str = Field("", title="Join progress message. May be error.")
    error: bool = Field(False, title="Progress is in error state.")


class JoinRequestParamsModel(BaseModel):
    uuid: UUID = Field(title="Requesting node's UUID.")
    hostname: str = Field(title="Requesting node's hostname.")
    address: str = Field(title="Requesting node's IP address.")
    token: str = Field(title="Cluster token.")


class JoinRequestReplyModel(BaseModel):
    pubkey: str = Field(title="Cluster's public key.")
    cephconf: str = Field(title="Ceph configuration.")
    keyring: str = Field(title="Ceph keyring.")


class JoinReadyParamsModel(BaseModel):
    uuid: UUID = Field(title="Requesting node's UUID.")


class JoinReadyReplyModel(BaseModel):
    success: bool = Field(title="Whether the node was successfully added.")
    msg: str = Field(title="A response message, if any.")


class ProgressEnum(int, Enum):
    START = 0  # start joining process
    CONFIGURE = 1  # configure the node
    CONTAINERS = 2  # obtain containers
    ADDING = 3  # request adding to cluster
    JOINING = 4  # joining the (ceph) cluster
    ASSIMILATE = 5  # assimilate devices
    DONE = 6  # fully joined


class JoinRequestState(int, Enum):
    NONE = 0
    STARTED = 1
    ADDED = 2


class JoinRequestEntry(BaseModel):
    hostname: str
    address: str
    state: JoinRequestState
    last_seen: dt


class JoinRequestMgr:
    """
    Controls the joining procedure from the node requesting to join. Can only
    happen if the node has been installed, but never participated in the
    cluster.
    """

    _gstate: GlobalState
    _nodemgr: NodeMgr
    _done: bool
    _session: requests.Session
    _task: Optional[asyncio.Task]
    _progress: Optional[JoinProgress]

    _progress_bounds: Dict[ProgressEnum, int] = {
        ProgressEnum.START: 0,
        ProgressEnum.CONFIGURE: 25,
        ProgressEnum.CONTAINERS: 30,
        ProgressEnum.ADDING: 50,
        ProgressEnum.JOINING: 60,
        ProgressEnum.ASSIMILATE: 70,
        ProgressEnum.DONE: 100,
    }

    def __init__(self, gstate: GlobalState, nodemgr: NodeMgr) -> None:
        self._gstate = gstate
        self._nodemgr = nodemgr
        self._done = False
        self._session = requests.Session()
        self._task = None
        self._progress = None

    @property
    def done(self) -> bool:
        return (
            self._task is not None
            and self._task.done()
            and (
                self._done
                or (self._progress is not None and self._progress.error)
            )
        )

    @property
    def progress(self) -> JoinProgress:
        if not self._progress:
            return JoinProgress()
        return self._progress

    async def wait(self) -> JoinProgress:
        if self._task is not None:
            logger.info("Waiting for task to finish.")
            await self._task
            self._task = None
        return self.progress

    async def die(self) -> None:
        if self._task is None:
            return
        logger.info("Asking task to cancel.")
        self._task.cancel()

    async def join(
        self,
        remote_addr: str,
        token: str,
        addr: str,
        hostname: str,
        storage: List[str],
    ) -> None:
        """
        Reach out to the node at the specified address and request to join.
        We'll need to provide the token and our hostname, and wait for a reply
        containing the required data to access the cluster.
        """
        if self._task is not None:
            raise AlreadyJoiningError("Node is already joining.")
        elif self.done:
            raise AlreadyJoinedError("Node already joined.")

        assert remote_addr is not None
        assert addr is not None
        assert token is not None
        assert hostname is not None

        remote_addr = remote_addr.strip()
        addr = addr.strip()
        token = token.strip()
        hostname = hostname.strip()

        if not remote_addr or not addr or not token or not hostname:
            raise ValueError()

        self._task = asyncio.create_task(
            self._join_task(remote_addr, token, addr, hostname, storage)
        )

    async def _join_task(
        self,
        remote: str,
        token: str,
        addr: str,
        hostname: str,
        storage: List[str],
    ) -> None:
        """Handle the join process as a separate task."""
        self._progress = JoinProgress(
            joined=False, progress=0, error=False, msg=""
        )
        self._mark_progress(ProgressEnum.START, "Start joining.")

        proto = "https://"
        if remote.startswith("https://") or remote.startswith("http://"):
            proto = ""
        params = JoinRequestParamsModel(
            uuid=self._nodemgr.uuid,
            hostname=hostname,
            address=addr,
            token=token,
        )
        try:
            ep = f"{proto}{remote}/api/deploy/join/request"
            req = self._session.post(ep, data=params.json())
        except requests.exceptions.SSLError:
            self._mark_error("SSL Error.")
            return
        except requests.exceptions.ConnectionError:
            self._mark_error("Unable to connect.")
            return

        if not req.ok:
            self._mark_error(req.reason)
            return

        try:
            details = JoinRequestReplyModel.parse_raw(req.text)
        except ValidationError:
            logger.error(f"Unable to parse response from {remote}.")
            self._mark_error("Unable to parse response.")
            return

        assert details.pubkey
        assert details.keyring
        assert details.cephconf

        self._mark_progress(ProgressEnum.CONFIGURE, "Configuring node.")
        self._write_keys(details.pubkey, details.keyring, details.cephconf)

        try:
            await self._prepare_node(hostname)
        except JoinError as e:
            logger.error(f"Error preparing node: {e.message}")
            self._mark_error(e.message)
            return

        self._mark_progress(ProgressEnum.CONTAINERS, "Obtaining containers.")
        ctrcfg = self._gstate.config.options.containers
        try:
            await container_pull(ctrcfg.registry, ctrcfg.image)
        except ContainerPullError as e:
            logger.error(f"Error pulling containers: {e.message}")
            self._mark_error(e.message)
            return

        self._mark_progress(ProgressEnum.ADDING, "Ready to join the cluster.")
        params = JoinReadyParamsModel(uuid=self._nodemgr.uuid)
        try:
            ep = f"{proto}{remote}/api/deploy/join/ready"
            req = self._session.post(ep, data=params.json())
        except requests.exceptions.SSLError:
            self._mark_error("SSL Error.")
            return
        except requests.exceptions.ConnectionError:
            self._mark_error("Unable to connect.")
            return

        if not req.ok:
            self._mark_error(req.reason)
            return

        try:
            ack = JoinReadyReplyModel.parse_raw(req.text)
        except ValidationError:
            logger.error(f"Unable to parse ready response from {remote}.")
            self._mark_error("Unable to parse response.")
            return

        if not ack.success:
            logger.error(f"Error adding node: {ack.msg}")
            self._mark_error(f"Unable to join: {ack.msg}")
            return

        self._mark_progress(ProgressEnum.JOINING, "Joining the system.")
        orch = Orchestrator(self._gstate.ceph_mgr)
        try:
            await asyncio.wait_for(orch.wait_host_added(hostname), 30.0)
        except TimeoutError:
            logger.error("Timeout waiting for host added to cluster.")
            self._mark_error("Unable to join: timed out.")
            return

        self._mark_progress(
            ProgressEnum.ASSIMILATE, "Assimilating storage devices."
        )
        logger.debug(f"Assimilating storage devices: {storage}")
        try:
            orch.assimilate_devices(hostname, storage)
            while not orch.devices_assimilated(hostname, storage):
                await asyncio.sleep(1.0)
        except CephCommandError as e:
            logger.error(f"Failed assimilating devices: {e.message}")
            self._mark_error("Failed assimilating storage devices.")
            return

        self._mark_progress(ProgressEnum.DONE, "Joined.")

    async def _prepare_node(self, hostname: str) -> None:
        """Prepare the node."""
        assert hostname is not None and len(hostname) > 0
        assert self._gstate is not None

        try:
            await set_hostname(hostname)
        except HostnameCtlError as e:
            msg = f"Error setting hostname during join: {e.message}"
            logger.error(msg)
            raise JoinError(msg)
        except Exception as e:
            msg = f"Unknown error setting hostname during join: {str(e)}"
            logger.error(msg)
            raise JoinError(msg)

        store = self._gstate.store
        await store.ensure_connection()
        logger.debug("Obtain NTP address from store.")
        ntpaddr = await store.get("/nodes/ntp_addr")
        logger.debug(f"NTP address is '{ntpaddr}'")
        assert ntpaddr is not None and len(ntpaddr) > 0

        try:
            await set_ntp_addr(ntpaddr)
        except NodeChronyRestartError as e:
            msg = f"Error setting NTP address: {e.message}"
            logger.error(msg)
            raise JoinError(msg)

        ctrcfg_str = await store.get("/nodes/containers")
        assert ctrcfg_str is not None and len(ctrcfg_str) > 0
        ctrcfg = ContainersOptionsModel.parse_raw(ctrcfg_str)
        self._gstate.config.options.containers = ctrcfg
        try:
            await set_registry(ctrcfg.registry, ctrcfg.secure)
        except ContainerError as e:
            msg = f"Error setting container registry: {e.message}"
            logger.error(msg)
            raise JoinError(msg)

    def _write_keys(self, pubkey: str, keyring: str, cephconf: str) -> None:
        authorized_keys = Path("/root/.ssh/authorized_keys")
        authorized_keys.parent.mkdir(exist_ok=True, parents=True, mode=0o700)
        with authorized_keys.open("a") as fd:
            fd.writelines([pubkey])
            logger.debug(f"prepare_node: wrote pubkey to {authorized_keys}")

        # write ceph.conf, allows accessing the cluster
        confpath = Path("/etc/ceph/ceph.conf")
        keyringpath = Path("/etc/ceph/ceph.client.admin.keyring")
        confpath.parent.mkdir(exist_ok=True, parents=True, mode=0o755)
        confpath.write_text(cephconf)
        keyringpath.write_text(keyring)
        keyringpath.chmod(0o600)
        confpath.chmod(0o644)

    def _mark_progress(self, stage: ProgressEnum, msg: str) -> None:
        """Mark progress on join."""
        assert self._progress is not None
        value: int = self._progress_bounds[stage]
        self._progress.progress = value
        self._progress.msg = msg

    def _mark_error(self, msg: str) -> None:
        """Mark progress error."""
        logger.error(f"Join error: {msg}")
        assert self._progress is not None
        self._progress.error = True
        self._progress.msg = msg
        self._progress.joined = False
        self._progress.progress = 0


class JoinHandlerMgr:
    """
    Controls the join procedure from the node handling a join request. Can only
    happen if the node handling the join has been installed and is
    participating in the cluster.
    """

    _requests: Dict[UUID, JoinRequestEntry]
    _gstate: GlobalState

    def __init__(self, gstate: GlobalState) -> None:
        self._requests = {}
        self._gstate = gstate

    def prune(self) -> None:
        now = dt.utcnow()
        for uuid, entry in self._requests.items():
            delta = now - entry.last_seen
            if delta.seconds > 300:  # 5 minutes
                logger.info(f"Pruning join request for node '{uuid}'")
                del self._requests[uuid]

    async def handle_request(
        self, uuid: UUID, hostname: str, addr: str, token: str
    ) -> JoinRequestReplyModel:
        """Handle a join request from another node."""
        # these must have been validated before reaching us.
        assert hostname
        assert addr
        assert token

        store: KV = self._gstate.store
        cluster_token = await store.get("/nodes/token")
        assert cluster_token is not None and len(cluster_token) > 0

        if token != cluster_token:
            raise BadTokenError()

        # Node might have died before finishing joining the cluster.
        # Check whether we finished the join, and refuse if so.
        # Otherwise, allow the node to join as if it was the first time.
        if (
            uuid in self._requests
            and self._requests[uuid].state >= JoinRequestState.ADDED
        ):
            raise AlreadyJoinedError("Node has already joined.")

        orch: Orchestrator = Orchestrator(self._gstate.ceph_mgr)
        try:
            exists = orch.host_exists(hostname)
        except Exception as e:
            logger.error(f"Error checking whether host exists: {str(e)}")
            raise JoinError("Unable to check whether host exists.")

        if exists:
            logger.debug(f"Node with hostname '{hostname}' already exists.")
            raise HostnameExistsError("Hostname already exists in cluster.")

        pubkey = orch.get_public_key()
        assert pubkey is not None and len(pubkey) > 0

        cephconf_path: Path = Path("/etc/ceph/ceph.conf")
        keyring_path: Path = Path("/etc/ceph/ceph.client.admin.keyring")
        assert cephconf_path.exists()
        assert keyring_path.exists()

        cephconf: str = cephconf_path.read_text("utf-8")
        keyring: str = keyring_path.read_text("utf-8")
        assert len(cephconf) > 0
        assert len(keyring) > 0

        self._requests[uuid] = JoinRequestEntry(
            hostname=hostname,
            address=addr,
            state=JoinRequestState.STARTED,
            last_seen=dt.utcnow(),
        )

        return JoinRequestReplyModel(
            pubkey=pubkey, cephconf=cephconf, keyring=keyring
        )

    async def handle_ready(self, uuid: UUID) -> None:
        """
        Handle Ready Request from a node with given UUID. If we know about
        the node, we will finish their join process.
        """
        if uuid not in self._requests:
            raise NotJoiningError(
                "Node doesn't have an active Join request on-going."
            )

        req = self._requests[uuid]
        orch = Orchestrator(self._gstate.ceph_mgr)
        exists = True
        addr = None
        try:
            addr = orch.get_host_addr(req.hostname)
        except UnknownHostError as e:
            exists = False
        except Exception as e:
            logger.error(f"Error checking whether host exists: {str(e)}")
            raise JoinError("Unable to check whether host exists.")

        if exists:
            assert addr is not None
            if addr == req.address:
                # Host has already been added, this is a no-op.
                return
            else:
                raise HostnameExistsError(
                    "Host exists with a different address."
                )

        if not orch.host_add(req.hostname, req.address):
            logger.error(
                f"Error adding host '{req.hostname}' with address "
                "'{req.address} to cluster."
            )
            raise JoinError("Unable to add host to cluster.")

        mon = self._gstate.ceph_mon
        if not mon.set_replicated_ruleset():
            logger.error(
                "Unable to set replicated ruleset for multi-node cluster."
            )
            return
        await self._set_pool_default_size()

    async def _set_pool_default_size(self) -> None:
        """reset the osd pool default size"""

        def get_target_size():
            orch: Orchestrator = Orchestrator(self._gstate.ceph_mgr)
            orch_hosts: List[OrchHostListModel] = orch.host_ls()
            return 2 if len(orch_hosts) < 3 else 3

        mon = self._gstate.ceph_mon
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

        for pool in mon.get_pools():  # all pools
            msg = (
                "set osd pool size >"
                f" pool: {pool.pool_name}"
                f" current_size: {pool.size}"
                f" target_size: {target_size}"
            )

            if pool.size > target_size:
                reason = "reason: pool is user defined"
                logger.debug(f"skipping {msg} {reason}")
                continue

            logger.info(msg)
            mon.set_pool_size(pool.pool_name, target_size)
