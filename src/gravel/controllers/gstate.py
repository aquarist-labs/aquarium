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
import time
from abc import ABC, abstractmethod
import logging.config
from logging import Logger
from typing import Dict
from fastapi.logger import logger as fastapi_logger

from gravel.controllers.config import Config
from gravel.controllers.kv import KV


logger: Logger = fastapi_logger


def setup_logging(console_level: str) -> None:
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "[%(levelname)-5s] %(asctime)s -- %(module)s -- %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S"
            },
            "colorized": {
                "()": "uvicorn.logging.ColourizedFormatter",
                "format": "%(levelprefix)s %(asctime)s -- %(module)s -- %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
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
                "backupCount": 1
            }
        },
        "loggers": {
            "uvicorn": {
                "level": "DEBUG",
                "handlers": ["console", "log_file"],
                "propagate": "no"
            }
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "log_file"]
        }
    }

    logging.config.dictConfig(logging_config)


class Ticker(ABC):

    def __init__(self, name: str, tick_interval: float):
        self._last_tick: float = 0
        self._tick_interval: float = tick_interval
        self._is_ticking: bool = False
        gstate.add_ticker(name, self)

    @abstractmethod
    async def _do_tick(self) -> None:
        pass

    @abstractmethod
    async def _should_tick(self) -> bool:
        pass

    async def tick(self) -> None:
        now: float = time.monotonic()
        diff: float = (now - self._last_tick)
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


class GlobalState:

    _config: Config
    _is_shutting_down: bool
    _tickers: Dict[str, Ticker]
    _kvstore: KV

    def __init__(self):
        self._config = Config()
        self._is_shutting_down = False
        self._tickers = {}
        self._kvstore = KV()

    async def start(self) -> None:
        if self._is_shutting_down:
            return
        self.tick_task = asyncio.create_task(self.tick())

    async def shutdown(self) -> None:
        self._is_shutting_down = True
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

    async def init_store(self) -> None:
        await self._kvstore.ensure_connection()

    @property
    def config(self) -> Config:
        return self._config

    @property
    def store(self) -> KV:
        return self._kvstore


gstate: GlobalState = GlobalState()
