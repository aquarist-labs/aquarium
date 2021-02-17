# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from logging import Logger
import time
from typing import Optional
from fastapi.logger import logger as fastapi_logger
from gravel.cephadm.models import NodeInfoModel
from gravel.controllers.gstate import gstate, Ticker
from gravel.cephadm.cephadm import Cephadm


logger: Logger = fastapi_logger


class Inventory(Ticker):

    _latest: Optional[NodeInfoModel]

    def __init__(self):
        self.is_ticking = False
        self._latest = None
        self.probe_interval = gstate.config.options.inventory_probe_interval
        self.last_probe: int = 0
        gstate.add_ticker("inventory", self)

    async def tick(self) -> None:
        if self.is_ticking:
            return

        now: int = int(time.monotonic())
        if self.last_probe > 0 and \
           (now - self.last_probe) < self.probe_interval:
            return

        self.is_ticking = True

        await self.probe()
        self.last_probe = int(time.monotonic())

        self.is_ticking = False
        pass

    async def probe(self) -> None:
        cephadm: Cephadm = Cephadm()
        start: int = int(time.monotonic())
        nodeinfo = await cephadm.get_node_info()
        diff: int = int(time.monotonic()) - start
        logger.info(f"=> inventory probing took {diff} seconds")
        self._latest = nodeinfo

    async def latest(self) -> Optional[NodeInfoModel]:
        return self._latest
