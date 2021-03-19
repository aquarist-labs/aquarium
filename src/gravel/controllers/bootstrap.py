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
from fastapi.logger import logger as fastapi_logger

from gravel.cephadm.cephadm import Cephadm
from gravel.controllers.nodes.errors import (
    NodeCantBootstrapError,
    NodeNotStartedError
)
from gravel.controllers.nodes.mgr import (
    NodeMgr,
    NodeStageEnum,
    get_node_mgr
)


logger: Logger = fastapi_logger  # required to provide type-hint to pylance


class NetworkAddressNotFoundError(Exception):
    pass


class BootstrapError(Exception):
    pass


class BootstrapStage(int, Enum):
    NONE = 0
    RUNNING = 1
    DONE = 2
    ERROR = 3


class Bootstrap:

    stage: BootstrapStage
    progress: int

    def __init__(self):
        self.stage = BootstrapStage.NONE
        self.progress = 0
        pass

    async def _should_bootstrap(self) -> bool:
        nodemgr = get_node_mgr()
        stage: NodeStageEnum = nodemgr.stage
        return stage == NodeStageEnum.NONE

    async def _is_bootstrapping(self) -> bool:
        nodemgr = get_node_mgr()
        return nodemgr.bootstrapping

    async def bootstrap(self) -> bool:
        logger.debug("do bootstrap")

        mgr: NodeMgr = get_node_mgr()
        stage: NodeStageEnum = mgr.stage
        if stage > NodeStageEnum.NONE:  # no longer vanilla, can't bootstrap
            return False

        try:
            await mgr.prepare_bootstrap()
        except NodeCantBootstrapError:
            logger.error("Can't bootstrap node")
            return False
        except NodeNotStartedError:
            logger.error("Node can't bootstrap yet")
            return False

        try:
            asyncio.create_task(self._do_bootstrap())
        except Exception as e:
            logger.error(f"error starting bootstrap task: {str(e)}")
            return False

        return True

    async def get_stage(self) -> BootstrapStage:
        return self.stage

    async def get_progress(self) -> int:
        return self.progress

    async def _do_bootstrap(self) -> None:
        mgr: NodeMgr = get_node_mgr()
        address = mgr.address

        logger.info(f"address: {address}")
        assert address is not None and len(address) > 0

        mgr: NodeMgr = get_node_mgr()
        assert mgr.stage == NodeStageEnum.NONE
        await mgr.start_bootstrap()  # XXX: needs hostname

        self.stage = BootstrapStage.RUNNING

        def progress_cb(percent: int) -> None:
            logger.debug(f"bootstrap > {percent}%")
            self.progress = percent

        retcode: int = 0
        try:
            cephadm: Cephadm = Cephadm()
            _, _, retcode = await cephadm.bootstrap(address, progress_cb)
        except Exception as e:
            raise BootstrapError(e) from e

        if retcode != 0:
            raise BootstrapError(f"error bootstrapping: rc = {retcode}")

        self.stage = BootstrapStage.DONE
        await get_node_mgr().finish_bootstrap()
