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

from logging import Logger
from typing import Optional
from fastapi.logger import logger as fastapi_logger

from gravel.controllers.gstate import (
    Ticker,
    gstate
)
from gravel.controllers.orch.ceph import Mon
from gravel.controllers.orch.models import (
    CephStatusModel
)
from gravel.controllers.nodes.mgr import (
    NodeMgr,
    NodeStageEnum,
    get_node_mgr
)


logger: Logger = fastapi_logger


class CephStatusNotAvailableError(Exception):
    pass


class Status(Ticker):

    _latest: Optional[CephStatusModel]
    _mon: Optional[Mon]

    def __init__(self):
        super().__init__(
            "status",
            gstate.config.options.status.probe_interval
        )
        self._mon = None
        self._latest = None

    async def _do_tick(self) -> None:

        if not self._mon:
            self._mon = Mon()

        await self.probe()

    async def _should_tick(self) -> bool:
        nodemgr: NodeMgr = get_node_mgr()
        return nodemgr.stage >= NodeStageEnum.BOOTSTRAPPED

    async def probe(self) -> None:
        assert self._mon
        self._latest = self._mon.status

    @property
    def status(self) -> CephStatusModel:
        if not self._latest:
            raise CephStatusNotAvailableError()
        return self._latest


_status = Status()


def get_status_ctrl() -> Status:
    global _status
    return _status
