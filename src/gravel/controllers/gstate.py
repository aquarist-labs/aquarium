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

import asyncio
import logging.config
import time
import typing
from abc import ABC, abstractmethod
from logging import Logger
from typing import Dict, Type

from fastapi.logger import logger as fastapi_logger

from gravel.cephadm.cephadm import Cephadm
from gravel.controllers.ceph.ceph import Mgr, Mon
from gravel.controllers.config import Config
from gravel.controllers.kv import KV

if typing.TYPE_CHECKING:
    from gravel.controllers.inventory.inventory import Inventory
    from gravel.controllers.resources.devices import Devices
    from gravel.controllers.resources.network import Network
    from gravel.controllers.resources.status import Status
    from gravel.controllers.resources.storage import Storage

logger: Logger = fastapi_logger


def setup_logging(console_level: str) -> None:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": (
                    "[%(levelname)-5s] %(asctime)s -- "
                    "%(module)s -- %(message)s"
                ),
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
            "colorized": {
                "()": "uvicorn.logging.ColourizedFormatter",
                "format": (
                    "%(levelprefix)s %(asctime)s -- "
                    "%(module)s -- %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "level": console_level,
                "class": "logging.StreamHandler",
                "formatter": "colorized",
            },
            "log_file": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "simple",
                "filename": "/tmp/aquarium.log",
                "maxBytes": 10485760,
                "backupCount": 1,
            },
        },
        "loggers": {
            "uvicorn": {
                "level": "DEBUG",
                "handlers": ["console", "log_file"],
                "propagate": "no",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["console", "log_file"]},
    }

    logging.config.dictConfig(logging_config)


class Ticker(ABC):
    def __init__(self, probe_interval: float):
        self._last_tick: float = 0
        self._tick_interval: float = probe_interval
        self._is_ticking: bool = False

    @abstractmethod
    async def _do_tick(self) -> None:
        pass

    @abstractmethod
    async def _should_tick(self) -> bool:
        pass

    async def tick(self) -> None:
        now: float = time.monotonic()
        diff: float = now - self._last_tick
        if diff < self._tick_interval or self._is_ticking:
            return

        if not await self._should_tick():
            return

        self._is_ticking = True
        await self._do_tick()
        self._is_ticking = False
        self._last_tick = time.monotonic()

    async def shutdown(self) -> None:
        pass

    def set_tick_interval(self, new_interval: float) -> None:
        self._tick_interval = new_interval


class GlobalState:

    _config: Config
    _is_shutting_down: bool
    _tickers: Dict[str, Ticker]
    _kvstore: KV
    devices: Devices
    status: Status
    inventory: Inventory
    network: Network
    storage: Storage
    cephadm: Cephadm
    ceph_mgr: Mgr
    ceph_mon: Mon

    def __init__(self, kv_class: Type[KV] = KV):
        self._config = Config()
        self._is_shutting_down = False
        self._tickers = {}
        self._kvstore = kv_class()

    def add_cephadm(self, cephadm: Cephadm):
        self.cephadm = cephadm

    def add_ceph_mgr(self, mgr: Mgr):
        self.ceph_mgr = mgr

    def add_ceph_mon(self, ceph_mon: Mon):
        self.ceph_mon = ceph_mon

    def add_devices(self, devices: Devices):
        self.devices = devices
        self.add_ticker("devices", devices)

    def add_status(self, status: Status):
        self.status = status
        self.add_ticker("status", status)

    def add_inventory(self, inventory: Inventory):
        self.inventory = inventory
        self.add_ticker("inventory", inventory)

    def add_network(self, network: Network):
        self.network = network
        self.add_ticker("network", network)

    def add_storage(self, storage: Storage):
        self.storage = storage
        self.add_ticker("storage", storage)

    async def start(self) -> None:
        if self._is_shutting_down:
            return
        self._kvstore.start()
        self.tick_task = asyncio.create_task(self.tick())

    async def shutdown(self) -> None:
        self._is_shutting_down = True
        await self._kvstore.close()
        logger.info("shutdown!")
        await self.tick_task

    async def tick(self) -> None:
        while not self._is_shutting_down:
            logger.debug("tick")
            await asyncio.sleep(1)
            await self._do_ticks()

        logger.info("tick shutting down")
        await self._shutdown_tickers()

    async def _do_ticks(self) -> None:
        for desc, ticker in self._tickers.items():
            logger.debug(f"tick {desc}")
            asyncio.create_task(ticker.tick())

    async def _shutdown_tickers(self) -> None:
        for desc, ticker in self._tickers.items():
            logger.debug(f"shutdown ticker {desc}")
            await ticker.shutdown()

    def add_ticker(self, desc: str, whom: Ticker) -> None:
        if desc not in self._tickers:
            self._tickers[desc] = whom

    def rm_ticker(self, desc: str) -> None:
        if desc in self._tickers:
            del self._tickers[desc]

    def get_ticker(self, desc: str) -> Ticker:
        return self._tickers[desc]

    @property
    def config(self) -> Config:
        return self._config

    @property
    def store(self) -> KV:
        return self._kvstore
