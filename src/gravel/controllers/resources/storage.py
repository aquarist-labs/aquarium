# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import time
from typing import Dict
from gravel.controllers.gstate import Ticker
from gravel import gstate
from gravel.controllers.orch.ceph import Mon


class Storage(Ticker):

    def __init__(self):
        self._is_ticking: bool = False
        self._last_tick: float = 0
        gstate.add_ticker("storage", self)

    async def tick(self) -> None:
        now: float = time.monotonic()
        diff: float = now - self._last_tick
        if diff < gstate.config.options.storage_probe_interval or \
           self._is_ticking:
            return
        self._is_ticking = True
        await self._update()
        self._is_ticking = False
        self._last_tick = time.monotonic()

    @property
    def available(self) -> int:
        return 0

    @property
    def used(self) -> int:
        return 0

    @property
    def total(self) -> int:
        return 0

    async def usage(self) -> Dict[str, int]:
        return {
            "nfs-foobar": 123,
            "cephfs-baz": 456
        }

    async def _update(self) -> None:
        mon = Mon()
        result = mon.df()
        assert len(result) >= 0
