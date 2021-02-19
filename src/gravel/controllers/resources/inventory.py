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
        super().__init__(
            "inventory",
            gstate.config.options.inventory_probe_interval
        )
        self._latest = None

    async def _do_tick(self) -> None:
        await self.probe()

    async def _should_tick(self) -> bool:
        return True

    async def probe(self) -> None:
        cephadm: Cephadm = Cephadm()
        start: int = int(time.monotonic())
        nodeinfo = await cephadm.get_node_info()
        diff: int = int(time.monotonic()) - start
        logger.info(f"=> inventory probing took {diff} seconds")
        self._latest = nodeinfo

    async def latest(self) -> Optional[NodeInfoModel]:
        return self._latest
