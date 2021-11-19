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

import asyncio
from enum import Enum
from json import JSONDecodeError
from logging import Logger
from pathlib import Path
from typing import List, Optional

from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field
from pydantic.error_wrappers import ValidationError
from gravel.controllers.deployment.create import (
    AlreadyCreatingError,
    ContainerConfig,
    CreateConfig,
    CreateStateEnum,
    CreationError,
    DeploymentCreator,
)

from gravel.controllers.errors import GravelError
from gravel.controllers.gstate import GlobalState
from gravel.controllers.inventory.disks import DiskDevice, get_storage_devices
from gravel.controllers.nodes.mgr import NodeMgr
from gravel.controllers.nodes.requirements import (
    RequirementsModel,
    localhost_qualified,
)
from gravel.controllers.nodes.systemdisk import (
    MountError,
    OverlayError,
    SystemDisk,
    UnavailableDeviceError,
    UnknownDeviceError,
)
from gravel.controllers.utils import read_model, write_model

"""
Handles all steps of deployment for this node, from a bare metal system to an
installed system. We will keep track of information that is relevant to track
the deployment state, and will persist it as needed.
"""

CONFDIR = "/etc/aquarium"


logger: Logger = fastapi_logger


class InitStateEnum(int, Enum):
    NONE = 0
    INSTALLED = 1
    DEPLOYED = 2


class DeploymentStateEnum(int, Enum):
    NONE = 0
    INSTALLING = 1
    INSTALLED = 2
    DEPLOYING = 3
    DEPLOYED = 4


class DeploymentErrorEnum(int, Enum):
    NONE = 0
    DEVICE_UNKNOWN = 1
    DEVICE_UNAVAILABLE = 2
    UNKNOWN_ERROR = 3
    ENABLING = 4
    CREATING = 5


class DeploymentStateModel(BaseModel):
    init: InitStateEnum = Field(InitStateEnum.NONE, title="Init state.")
    deployment: DeploymentStateEnum = Field(
        DeploymentStateEnum.NONE, title="Deployment state."
    )


class ProgressModel(BaseModel):
    value: int = Field(0, title="Current progress percentage.")
    msg: str = Field("", title="Current progress message.")


class DeploymentErrorModel(BaseModel):
    code: DeploymentErrorEnum = Field(
        DeploymentErrorEnum.NONE, title="Deployment error code."
    )
    msg: str = Field("", title="Deployment error message, if any.")


class DeploymentStatusModel(BaseModel):
    state: DeploymentStateModel = Field(
        DeploymentStateModel(), title="Current deployment state."
    )
    progress: Optional[ProgressModel] = Field(
        None, title="Insights into current progress."
    )
    error: DeploymentErrorModel = Field(
        DeploymentErrorModel(), title="Current deployment error."
    )


class DeploymentError(GravelError):
    pass


class AlreadyInitedError(DeploymentError):
    pass


class AlreadyPreInitedError(DeploymentError):
    pass


class InitError(DeploymentError):
    pass


class NotPreInitedError(DeploymentError):
    pass


class NotPostInitedError(DeploymentError):
    pass


class NodeInstalledError(DeploymentError):
    pass


class NodeDeployedError(DeploymentError):
    pass


class NotReadyYetError(DeploymentError):
    pass


class DeploymentMgr:
    """Handles the deployment procedure for the node."""

    _init_state: InitStateEnum
    _deployment_state: DeploymentStateEnum
    _preinited: bool
    _inited: bool
    _postinited: bool
    _task_main: Optional[asyncio.Task]
    _task_install: Optional[asyncio.Task]
    _running: bool
    _error: DeploymentErrorModel
    _gstate: Optional[GlobalState]
    _nodemgr: Optional[NodeMgr]
    _creator: Optional[DeploymentCreator]

    def __init__(self) -> None:
        self._init_state = InitStateEnum.NONE
        self._deployment_state = DeploymentStateEnum.NONE
        self._preinited = False
        self._inited = False
        self._postinited = False
        self._task_main = None
        self._task_install = None
        self._running = False
        self._error = DeploymentErrorModel()
        self._gstate = None
        self._nodemgr = None
        self._creator = None

    @property
    def installed(self) -> bool:
        return self._init_state >= InitStateEnum.INSTALLED

    @property
    def deployed(self) -> bool:
        return self._init_state == InitStateEnum.DEPLOYED

    @property
    def state(self) -> DeploymentStateEnum:
        return self._deployment_state

    async def _task_main_func(self) -> None:
        while self._running:
            logger.debug("Checking deployment state")
            if self._task_install is not None and self._task_install.done():
                logger.debug("Install done.")
                ret: DeploymentErrorModel = await self._task_install
                if ret.code > DeploymentErrorEnum.NONE:
                    self._error = ret
                else:
                    self._deployment_state = DeploymentStateEnum.INSTALLED
                    self._init_state = InitStateEnum.INSTALLED
                self._task_install = None

            elif self._creator is not None and self._creator.done:
                logger.debug("Create done.")
                progress = await self._creator.wait()
                self._creator = None
                if progress.state == CreateStateEnum.CREATED:
                    self._init_state = InitStateEnum.DEPLOYED
                    self._deployment_state = DeploymentStateEnum.DEPLOYED
                    confdir = Path(CONFDIR)
                    write_model(
                        confdir,
                        "state",
                        DeploymentStateModel(
                            init=self._init_state,
                            deployment=self._deployment_state,
                        ),
                    )
                elif progress.error:
                    assert progress.progress == 0
                    logger.error(f"Error creating deployment: {progress.msg}")
                    self._error.msg = progress.msg
                    self._error.code = DeploymentErrorEnum.CREATING

            if self.deployed:
                break

            await asyncio.sleep(1.0)
        logger.debug("Main task done.")

    async def start_main_task(self) -> None:
        logger.debug("Starting main task.")
        if self._running:
            logger.warn("Attempting to start running main task.")
            return
        elif self._init_state >= InitStateEnum.DEPLOYED:
            logger.warn("Attempting to start main task on deployed node.")
            return
        self._running = True
        self._task_main = asyncio.create_task(self._task_main_func())

    async def stop_main_task(self) -> None:
        logger.debug("Stopping main task.")
        if not self._running:
            return
        assert self._task_main is not None
        self._running = False
        await self._task_main
        self._task_main = None
        if self._creator is not None:
            if self._creator.done:
                await self._creator.wait()
            else:
                await self._creator.die()
            self._creator = None

    async def shutdown(self) -> None:
        await self.stop_main_task()
        if self._task_install is not None:
            await self._task_install
            self._task_install = None

    async def preinit(self) -> None:
        """
        Prepare node init by checking for a System Disk and enabling it if
        found. Can only be called once, unless an error occurs.
        """

        if self._inited:
            raise AlreadyInitedError("Node has already been inited.")
        elif self._preinited:
            raise AlreadyPreInitedError("Node has already been pre-inited.")

        await self.start_main_task()
        assert self._running
        assert self._task_main is not None
        self._preinited = True

        sd = SystemDisk()
        if not await sd.exists():
            logger.info("System Disk not found, assuming fresh node.")
            return

        try:
            await sd.enable()
            logger.info("System Disk enabled.")
        except (OverlayError, MountError) as e:
            self._preinited = False
            raise DeploymentError(f"Error enabling System Disk: {e.message}")

        self._init_state = InitStateEnum.INSTALLED

    async def init(self) -> None:
        """
        Init the node's deployment. Only applicable if the system has been
        previously installed and persistent state exists. Otherwise the
        function returns, and the node will have to be installed.
        """

        if not self._preinited:
            raise NotPreInitedError("Node has not been pre-inited.")
        elif self._inited:
            raise AlreadyInitedError("Node has already been inited.")

        if self._init_state < InitStateEnum.INSTALLED:
            logger.info("Fresh system found. Requires install.")
            return

        logger.info("Initing node from on-disk state.")

        confdir = Path(CONFDIR)
        try:
            state: DeploymentStateModel = read_model(
                confdir, "state", DeploymentStateModel
            )
        except (ValidationError, JSONDecodeError):
            # On-disk model does not match our expectation. Do not init.
            raise InitError("Unable to parse on-disk state.")
        except (FileNotFoundError, NotADirectoryError):
            if confdir.exists() and not confdir.is_dir():
                # Something exists, but it's not a directory.
                raise InitError(f"'{confdir}' is not a directory.")
            elif not confdir.exists():
                confdir.mkdir(parents=True)

            # Missing on-disk state. This likely means the node died after
            # install but before being deployed. Let us write out a new state.
            logger.info("Missing State file, creating.")
            state = DeploymentStateModel(
                init=InitStateEnum.INSTALLED,
                deployment=DeploymentStateEnum.NONE,
            )
            write_model(confdir, "state", state)
        except FileExistsError:
            loc = confdir.joinpath("state.json")
            raise InitError(f"On-disk state is not a file at '{loc}'")

        self._init_state = state.init
        self._deployment_state = state.deployment
        self._inited = True

    def postinit(self, gstate: GlobalState, nodemgr: NodeMgr) -> None:
        """Called after all state has been inited, prepares for deployment."""
        assert gstate is not None
        assert gstate.ready
        assert nodemgr is not None
        assert self._running
        assert self._task_install is None
        assert self._init_state >= InitStateEnum.INSTALLED
        logger.debug("Post-init Deployment Manager.")
        self._gstate = gstate
        self._nodemgr = nodemgr
        self._postinited = True

    def get_status(self) -> DeploymentStatusModel:
        """Obtain node deployment status."""
        progress: Optional[ProgressModel] = None

        if self._creator is not None:
            create = self._creator.progress
            progress = ProgressModel(value=create.progress, msg=create.msg)

        return DeploymentStatusModel(
            state=DeploymentStateModel(
                init=self._init_state,
                deployment=self._deployment_state,
            ),
            progress=progress,
            error=self._error,
        )

    async def get_requirements(self) -> RequirementsModel:
        """Obtain node requirements."""
        return await localhost_qualified()

    async def get_devices(self) -> List[DiskDevice]:
        """Obtain storage devices."""
        try:
            return await get_storage_devices()
        except Exception:
            return []

    async def install(self, device: str) -> None:
        """Install Aquarium onto a specified device."""

        logger.debug(f"Attempt installing on {device}.")
        if self.installed:
            raise NodeInstalledError("Node is already installed.")
        if self._deployment_state >= DeploymentStateEnum.INSTALLING:
            logger.info("Node is currently installing; no op.")
            return

        assert self._task_main is not None
        assert not self._task_main.done()
        assert self._task_install is None

        # reset error, if any
        self._error = DeploymentErrorModel()
        self._task_install = asyncio.create_task(self._install_task(device))

    async def _install_task(self, device: str) -> DeploymentErrorModel:
        """Task responsible for asynchronously installing Aquarium."""

        logger.info(f"Start installing on device {device}.")
        self._deployment_state = DeploymentStateEnum.INSTALLING
        error: DeploymentErrorModel = DeploymentErrorModel()
        sd = SystemDisk()
        try:
            await sd.create(device)
        except UnknownDeviceError:
            error.code = DeploymentErrorEnum.DEVICE_UNKNOWN
            error.msg = f"Unknown device '{device}'"
        except UnavailableDeviceError as e:
            error.code = DeploymentErrorEnum.DEVICE_UNAVAILABLE
            error.msg = f"Device '{device}' is not available."
        except Exception as e:
            error.code = DeploymentErrorEnum.UNKNOWN_ERROR
            error.msg = f"Unknown error: {str(e)}"
        if error.code > DeploymentErrorEnum.NONE:
            self._deployment_state = DeploymentStateEnum.NONE
            return error

        logger.info(f"Enabling system disk from {device}")
        try:
            await sd.enable()
        except (OverlayError, MountError) as e:
            error.code = DeploymentErrorEnum.ENABLING
            error.msg = f"Unable to enable device '{device}: {e.message}"
            return error

        logger.info(f"Successfully installed and enabled device {device}.")
        assert error.code == DeploymentErrorEnum.NONE
        return error

    async def create(
        self,
        hostname: str,
        ntpaddr: str,
        containers: Optional[ContainerConfig],
        storage: List[str],
    ) -> None:
        """Create new deployment on current node."""

        logger.info("Attempt to create a new deployment.")
        if not self._postinited:
            raise NotPostInitedError("Node has not been post-inited.")
        elif self._init_state >= InitStateEnum.DEPLOYED:
            raise NodeDeployedError("Node has already been deployed.")
        elif self._deployment_state == DeploymentStateEnum.DEPLOYING:
            logger.info("Node already being deployed; no-op.")
            return

        assert self._nodemgr is not None
        if not self._nodemgr.available:
            raise NotReadyYetError("Node not ready yet.")

        assert self._gstate is not None
        assert self._creator is None
        self._creator = DeploymentCreator(self._gstate)

        addr: str = self._nodemgr.address
        assert addr is not None and len(addr) > 0

        config = CreateConfig(
            hostname=hostname,
            ntp_addr=ntpaddr,
            address=addr,
            storage=storage,
            container=containers,
        )

        try:
            await self._creator.create(config)
        except AlreadyCreatingError:
            logger.info("Already creating a new deployment.")
            return
        except CreationError as e:
            msg = f"Error creating a new deployment: {e.message}"
            logger.error(msg)
            raise DeploymentError(msg)

        self._deployment_state = DeploymentStateEnum.DEPLOYING
