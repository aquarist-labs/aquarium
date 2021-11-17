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
Creates a deployment on the current node.

"""

import asyncio
from enum import Enum
from logging import Logger
from typing import List, Optional

from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field
from gravel.controllers.ceph.ceph import CephCommandError, Mon
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
from gravel.controllers.nodes.host import set_hostname, HostnameCtlError
from gravel.controllers.nodes.ntp import set_ntp_addr, NodeChronyRestartError

logger: Logger = fastapi_logger


class CreationError(GravelError):
    pass


class AlreadyCreatingError(CreationError):
    pass


class ContainerConfig(BaseModel):
    url: str = Field(title="Container registry URL.")
    image: str = Field(title="Container image to use.")
    secure: bool = Field(title="Whether container registry is secure.")


class CreateConfig(BaseModel):
    hostname: str
    address: str
    ntp_addr: str
    storage: List[str] = Field([], title="Devices to consume for storage.")
    container: Optional[ContainerConfig]


class CreateStateEnum(int, Enum):
    NONE = 0
    CREATING = 1
    CREATED = 2
    ERROR = 3


class CreateProgress(BaseModel):
    state: CreateStateEnum = Field(
        CreateStateEnum.NONE, title="Creation state."
    )
    progress: int = Field(0, title="Creation progress percent.")
    msg: str = Field("", title="Create progress message. May be an error.")
    error: bool = Field(False, title="Progress is in an error state.")


class DeploymentCreator:
    """Manages the creation of a deployment on the node."""

    _gstate: GlobalState
    _task_create: Optional[asyncio.Task]
    _progress: Optional[CreateProgress]
    _bootstrapper: Optional[Bootstrap]
    _done: bool
    _hostname: Optional[str]
    _storage_devices: List[str]

    def __init__(self, gstate: GlobalState) -> None:
        self._gstate = gstate
        self._task_create = None
        self._progress = None
        self._bootstrapper = None
        self._done = False
        self._hostname = None
        self._storage_devices = []

    @property
    def progress(self) -> CreateProgress:
        """Return current progress. If none, return empty progress."""
        if not self._progress:
            return CreateProgress()
        return self._progress

    @property
    def done(self) -> bool:
        """Return whether we are done creating."""
        return (
            self._task_create is not None
            and self._task_create.done()
            and self._done
        )

    async def wait(self) -> CreateProgress:
        """Wait for completion."""
        if self._task_create is not None:
            logger.info("Waiting for task to finish.")
            await self._task_create
            self._task_create = None
        return self.progress

    async def die(self) -> None:
        """Force task to quit."""
        if self._task_create is None:
            return
        logger.info("Asking task to cancel.")
        self._task_create.cancel()

    async def create(self, config: CreateConfig) -> None:
        """Creates a new deployment."""

        if self._task_create is not None:
            raise AlreadyCreatingError("Deployment already being created.")

        assert config.hostname
        assert config.address
        assert config.ntp_addr
        assert config.storage is not None

        # keep track of hostname because we need it for post-bootstrap actions.
        self._hostname = config.hostname
        self._storage_devices = config.storage

        try:
            await self._prechecks(config.container)
        except Exception as e:
            logger.error(
                f"Unable to create deployment: pre-checks failed: {str(e)}"
            )
            raise CreationError("Pre-checks failed, unable to create.")

        self._progress = CreateProgress()
        self._task_create = asyncio.create_task(self._create_task_func(config))

    async def _prechecks(self, containers: Optional[ContainerConfig]) -> None:
        """
        Checks requirements for creation. Should be trivial, we can't block too
        long, otherwise the caller will be waiting. Longer checks should be
        performed within the creation task.
        """

        ctrcfg = self._gstate.config.options.containers
        if containers is not None:
            assert len(containers.url) > 0
            assert len(containers.image) > 0
            ctrcfg.registry = containers.url
            ctrcfg.secure = containers.secure
            ctrcfg.image = containers.image

        logger.debug(f"Preflight checks: {ctrcfg}")
        # propagate exceptions to caller, let them handle the various errors.
        await registry_check(ctrcfg.registry, ctrcfg.image, ctrcfg.secure)

    async def _create_task_func(self, config: CreateConfig) -> None:
        """Create a new deployment."""
        assert self._progress is not None
        assert self._progress.state == CreateStateEnum.NONE
        assert self._bootstrapper is None

        self._mark_state(CreateStateEnum.CREATING)
        self._mark_progress(0, "Starting to create new deployment.")
        try:
            await self._prepare_node(config.hostname, config.ntp_addr)
        except CreationError as e:
            self._mark_error(e.message)
            return
        self._mark_progress(25, "Deploying.")

        self._bootstrapper = Bootstrap(self._gstate)
        try:
            await self._bootstrapper.bootstrap(
                config.address, self._finish_bootstrap_cb
            )
        except BootstrapError as e:
            logger.error(f"Bootstrap error: {e.message}")
            self._mark_error(f"Error deploying: {e.message}")
            raise CreationError(f"Unable to bootstrap: {e.message}")
        logger.debug("Create task exit.")

    async def _prepare_node(self, hostname: str, ntpaddr: str) -> None:
        """
        Prepare the node. This must happen before bootstrapping the cluster.
        """
        assert hostname is not None and len(hostname) > 0
        assert ntpaddr is not None and len(ntpaddr) > 0

        try:
            await set_hostname(hostname)
        except HostnameCtlError as e:
            msg = f"Error setting hostname during create: {e.message}"
            logger.error(msg)
            raise CreationError(msg)
        except Exception as e:
            msg = f"Unknown error setting hostname during create: {str(e)}"
            logger.error(msg)
            raise CreationError(msg)

        try:
            await set_ntp_addr(ntpaddr)
        except NodeChronyRestartError as e:
            msg = f"Error setting NTP address: {e.message}"
            logger.error(msg)
            raise CreationError(msg)

        self._mark_progress(10, "Obtaining containers")
        ctrcfg = self._gstate.config.options.containers
        try:
            await set_registry(ctrcfg.registry, ctrcfg.secure)
            await container_pull(ctrcfg.registry, ctrcfg.image)
        except ContainerPullError as e:
            msg = f"Error obtaining containers: {e.message}"
            logger.error(msg)
            raise CreationError(msg)

    async def _finish_bootstrap_cb(
        self, success: bool, error: Optional[str]
    ) -> None:
        """
        Called once bootstrap is finished, allows us to configure the system to
        our needs.
        """
        if not success:
            logger.error(f"Bootstrap failed: {error}")
            self._mark_error(f"Failed deploying cluster: {error}")
            return
        logger.info(f"Bootstrap complete with success.")

        self._mark_progress(85, "Configuring deployment.")
        if not self._postbootstrap_config():
            self._mark_error("Failed configuring the deployment.")
            return

        self._mark_progress(90, "Assimilating storage devices.")
        if not await self._add_host():
            self._mark_error("Failed adding host to cluster.")
            return

        if not await self._assimilate_devices():
            self._mark_error("Failed assimilating storage devices.")
            return

        self._mark_progress(100, "Deployment Complete.")
        self._mark_state(CreateStateEnum.CREATED)
        self._done = True

    def _postbootstrap_config(self) -> bool:
        """Perform required post-bootstrap configurations."""
        mon: Mon = self._gstate.ceph_mon
        try:
            mon.set_allow_pool_size_one()
        except CephCommandError as e:
            logger.error(f"Unable to set 'allow pool size one': {str(e)}")
            return False

        try:
            mon.disable_warn_on_no_redundancy()
        except CephCommandError as e:
            logger.error("Unable to disable redundancy warning.")
            return False

        res: bool = mon.set_default_ruleset()
        if not res:
            logger.error("Unable to set default ruleset.")
            return False

        res = mon.config_set(
            "mgr", "mgr/cephadm/manage_etc_ceph_ceph_conf", "true"
        )
        if not res:
            logger.error("Unable to enable managed ceph.conf by cephadm.")
            return False

        res = mon.config_set(
            "global", "auth_allow_insecure_global_id_reclaim", "false"
        )
        if not res:
            logger.error("Unable to disable insecure global id reclaim.")
            return False

        ctrcfg = self._gstate.config.options.containers
        ctrimage = ctrcfg.get_image()
        assert ctrimage is not None and len(ctrimage) > 0
        res = mon.config_set("global", "container_image", ctrimage)
        if not res:
            logger.error("Unable to set global container image.")
            return False

        res = mon.module_enable("bubbles")
        if not res:
            logger.error("Unable to start Bubbles.")
            return False

        return True

    async def _add_host(self) -> bool:
        """Add current host to the cluster."""
        assert self._hostname is not None
        try:
            orch = Orchestrator(self._gstate.ceph_mgr)
            logger.debug("Wait for host to be added.")
            await asyncio.wait_for(orch.wait_host_added(self._hostname), 30.0)
        except TimeoutError:
            logger.error("Timed out waiting for host to be added.")
            return False
        return True

    async def _assimilate_devices(self) -> bool:
        """Assimilate storage devices."""
        assert self._hostname is not None
        if len(self._storage_devices) == 0:
            return True

        logger.debug(f"Assimilating storage devices: {self._storage_devices}")
        try:
            orch = Orchestrator(self._gstate.ceph_mgr)
            if not orch.host_exists(self._hostname):
                logger.error("Host is not part of the cluster.")
                return False
            orch.assimilate_devices(self._hostname, self._storage_devices)
            while not orch.devices_assimilated(
                self._hostname, self._storage_devices
            ):
                await asyncio.sleep(1.0)
        except CephCommandError as e:
            logger.error(
                f"Command error while assimilating devices: {e.message}"
            )
            return False
        return True

    def _mark_progress(self, value: int, msg: str) -> None:
        """Mark current progress."""
        logger.debug(f"Create progress: {value}%, {msg}")
        assert self._progress is not None
        self._progress.msg = msg
        self._progress.progress = value

    def _mark_state(self, state: CreateStateEnum) -> None:
        """Mark current progress state."""
        logger.debug(f"Create state change to {state}")
        # don't go back in state
        assert self._progress is not None
        assert self._progress.state <= state
        self._progress.state = state

    def _mark_error(self, msg: str) -> None:
        """Mark progress error."""
        logger.error(f"Create error: {msg}")
        assert self._progress is not None
        self._progress.state = CreateStateEnum.ERROR
        self._progress.progress = 0
        self._progress.error = True
        self._progress.msg = msg
