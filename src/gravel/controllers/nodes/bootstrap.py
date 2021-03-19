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
from typing import Awaitable, Callable, Optional
from fastapi.logger import logger as fastapi_logger

from gravel.cephadm.cephadm import Cephadm


logger: Logger = fastapi_logger  # required to provide type-hint to pylance


class BootstrapError(Exception):
    def __init__(self, msg: Optional[str] = ""):
        super().__init__()
        self._msg = msg

    @property
    def message(self) -> str:
        return self._msg if self._msg else "bootstrap error"


class BootstrapStage(int, Enum):
    NONE = 0
    RUNNING = 1
    DONE = 2
    ERROR = 3


class Bootstrap:

    _stage: BootstrapStage
    _progress: int

    def __init__(self):
        self._stage = BootstrapStage.NONE
        self._progress = 0
        pass

    async def bootstrap(
        self,
        address: str,
        cb: Callable[[bool, Optional[str]], Awaitable[None]]
    ) -> None:
        logger.debug(f"start bootstrapping, address: {address}")

        assert self._stage == BootstrapStage.NONE

        # TODO: check here if a cluster already exists, raise if so.

        try:
            asyncio.create_task(self._do_bootstrap(address, cb))
        except Exception as e:
            logger.error(f"error starting bootstrap task: {str(e)}")
            raise BootstrapError("error starting bootstrap task")

    @property
    def stage(self) -> BootstrapStage:
        return self._stage

    @property
    def progress(self) -> int:
        return self._progress

    async def _do_bootstrap(
        self,
        address: str,
        cb: Callable[[bool, Optional[str]], Awaitable[None]]
    ) -> None:
        logger.info(f"bootstrap address: {address}")
        assert address is not None and len(address) > 0

        self._stage = BootstrapStage.RUNNING

        def progress_cb(percent: int) -> None:
            logger.debug(f"bootstrap > {percent}%")
            self._progress = percent

        retcode: int = 0
        try:
            cephadm: Cephadm = Cephadm()
            _, _, retcode = await cephadm.bootstrap(address, progress_cb)
        except Exception as e:
            await cb(False, f"error bootstrapping: {str(e)}")
            self._stage = BootstrapStage.ERROR
            return

        if retcode != 0:
            await cb(False, f"error bootstrapping: rc = {retcode}")
            self._stage = BootstrapStage.ERROR
            return

        self._stage = BootstrapStage.DONE
        await cb(True, None)
