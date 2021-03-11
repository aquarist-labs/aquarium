# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from logging import Logger
import time
from typing import (
    Awaitable,
    Callable,
    List,
    Optional
)
from fastapi.logger import logger as fastapi_logger
from pydantic.main import BaseModel
from gravel.cephadm.models import NodeInfoModel
from gravel.controllers.gstate import gstate, Ticker
from gravel.cephadm.cephadm import Cephadm


logger: Logger = fastapi_logger


class Subscriber(BaseModel):
    cb: Callable[[NodeInfoModel], Awaitable[None]]
    once: bool


class Inventory(Ticker):

    _latest: Optional[NodeInfoModel]
    _subscribers: List[Subscriber]

    def __init__(self):
        super().__init__(
            "inventory",
            gstate.config.options.inventory.probe_interval
        )
        self._latest = None
        self._subscribers = []

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
        await self._publish()

    @property
    def latest(self) -> Optional[NodeInfoModel]:
        return self._latest

    def subscribe(
        self,
        cb: Callable[[NodeInfoModel], Awaitable[None]],
        once: bool
    ) -> None:
        self._subscribers.append(Subscriber(cb=cb, once=once))

    async def _publish(self) -> None:
        assert self._latest
        for subscriber in self._subscribers:
            # ignore type because mypy is somehow broken when doing callbacks
            # see https://github.com/python/mypy/issues/5485
            await subscriber.cb(self._latest)  # type: ignore
            if subscriber.once:
                self._subscribers.remove(subscriber)


_inventory = Inventory()


def get_inventory() -> Inventory:
    global _inventory
    return _inventory
