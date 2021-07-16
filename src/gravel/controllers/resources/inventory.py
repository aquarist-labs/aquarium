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

from __future__ import annotations
from logging import Logger
import time
from typing import Awaitable, Callable, List, Optional
from fastapi.logger import logger as fastapi_logger
from gravel.cephadm.models import NodeInfoModel
from gravel.controllers.gstate import Ticker, GlobalState
from gravel.cephadm.cephadm import Cephadm
from gravel.controllers.nodes.mgr import NodeMgr
from gravel.controllers.resources.inventory_sub import Subscriber


logger: Logger = fastapi_logger


class Inventory(Ticker):
    """
    Obtain host's inventory. Only runs once the node has been inited.

    Until the node is inited and is able to probe for the first time, will
    attempt to tick every 1.0 second. Once the first probe is finished, will
    reset its tick interval to the interval provided to the ctor (which will
    likely be the one passed through the config values).
    """

    _latest: Optional[NodeInfoModel]
    _subscribers: List[Subscriber]
    _nodemgr: NodeMgr
    _has_probed_once: bool
    _probe_interval: float
    _gstate: GlobalState

    def __init__(
        self, probe_interval: float, nodemgr: NodeMgr, gstate: GlobalState
    ):
        super().__init__(1.0)
        self._latest = None
        self._subscribers = []
        self._nodemgr = nodemgr
        self._has_probed_once = False
        self._probe_interval = probe_interval
        self._gstate = gstate

    async def _do_tick(self) -> None:
        await self.probe()
        if not self._has_probed_once:
            super().set_tick_interval(self._probe_interval)
            self._has_probed_once = True

    async def _should_tick(self) -> bool:
        return self._nodemgr.inited

    async def probe(self) -> None:
        cephadm: Cephadm = self._gstate.cephadm
        start: int = int(time.monotonic())
        nodeinfo = await cephadm.get_node_info()
        diff: int = int(time.monotonic()) - start
        logger.info(f"probing took {diff} seconds")
        self._latest = nodeinfo
        await self._publish()

    @property
    def latest(self) -> Optional[NodeInfoModel]:
        return self._latest

    async def subscribe(
        self, cb: Callable[[NodeInfoModel], Awaitable[None]], once: bool
    ) -> Optional[Subscriber]:
        # if we have available state, call back immediately.
        if self._latest:
            await cb(self._latest)  # type: ignore
            if once:
                return None
        sub = Subscriber(cb=cb, once=once)
        self._subscribers.append(sub)
        return sub

    def unsubscribe(self, sub: Subscriber) -> None:
        if sub in self._subscribers:
            self._subscribers.remove(sub)

    async def _publish(self) -> None:
        assert self._latest
        for subscriber in self._subscribers:
            # ignore type because mypy is somehow broken when doing callbacks
            # see https://github.com/python/mypy/issues/5485
            await subscriber.cb(self._latest)  # type: ignore
            if subscriber.once:
                self._subscribers.remove(subscriber)
