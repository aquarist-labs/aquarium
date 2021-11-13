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
from json import JSONDecodeError
from logging import Logger
from pathlib import Path
from typing import List

from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field
from pydantic.error_wrappers import ValidationError

from gravel.controllers.errors import GravelError
from gravel.controllers.inventory.disks import DiskDevice, get_storage_devices
from gravel.controllers.nodes.requirements import (
    RequirementsModel,
    localhost_qualified,
)
from gravel.controllers.nodes.systemdisk import (
    MountError,
    OverlayError,
    SystemDisk,
)
from gravel.controllers.utils import read_model, write_model

"""
Handles all steps of deployment for this node, from a bare metal system to an
installed system. We will keep track of information that is relevant to track
the deployment state, and will persist it as needed.
"""


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


class DeploymentStateModel(BaseModel):
    init: InitStateEnum = Field(InitStateEnum.NONE, title="Init state.")
    deployment: DeploymentStateEnum = Field(
        DeploymentStateEnum.NONE, title="Deployment state."
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


class DeploymentMgr:
    """Handles the deployment procedure for the node."""

    _init_state: InitStateEnum
    _deployment_state: DeploymentStateEnum
    _preinited: bool
    _inited: bool

    def __init__(self) -> None:
        self._init_state = InitStateEnum.NONE
        self._deployment_state = DeploymentStateEnum.NONE
        self._preinited = False
        self._inited = False

    @property
    def installed(self) -> bool:
        return self._init_state == InitStateEnum.INSTALLED

    @property
    def state(self) -> DeploymentStateEnum:
        return self._deployment_state

    async def preinit(self) -> None:
        """
        Prepare node init by checking for a System Disk and enabling it if
        found. Can only be called once, unless an error occurs.
        """

        if self._inited:
            raise AlreadyInitedError("Node has already been inited.")
        elif self._preinited:
            raise AlreadyPreInitedError("Node has already been pre-inited.")

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

        confdir = Path("/etc/aquarium")
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

    async def get_requirements(self) -> RequirementsModel:
        """Obtain node requirements."""
        return await localhost_qualified()

    async def get_devices(self) -> List[DiskDevice]:
        """Obtain storage devices."""
        try:
            return await get_storage_devices()
        except Exception:
            return []
