# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import asyncio
import time
from abc import ABC, abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor
from logging import Logger
from typing import Callable, Any, Dict
from fastapi.logger import logger as fastapi_logger

from gravel.controllers.config import Config


logger: Logger = fastapi_logger


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


class GlobalState:

    executor: ThreadPoolExecutor
    config: Config
    is_shutting_down: bool
    tickers: Dict[str, Ticker]

    def __init__(self):
        self.executor = ThreadPoolExecutor()
        self.config = Config()
        self.is_shutting_down = False
        self.tickers = {}

    async def start(self) -> None:
        if self.is_shutting_down:
            return
        self.tick_task = asyncio.create_task(self.tick())

    async def shutdown(self) -> None:
        self.is_shutting_down = True
        logger.info("shutdown!")
        await self.tick_task

    async def run_in_background(self,
                                func: Callable[[Any, Any], Any],
                                *args: Any
                                ):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(self.executor, func, *args)

    async def tick(self) -> None:
        while not self.is_shutting_down:
            state = self.config.deployment_state.stage
            logger.debug(f"=> tick ({state.name})")
            await asyncio.sleep(1)
            await self._do_ticks()

        logger.info("=> tick shutting down")

    async def _do_ticks(self) -> None:
        for desc, ticker in self.tickers.items():
            logger.debug(f"=> tick {desc}")
            asyncio.create_task(ticker.tick())

    def add_ticker(self, desc: str, whom: Ticker) -> None:
        if desc not in self.tickers:
            self.tickers[desc] = whom

    def rm_ticker(self, desc: str) -> None:
        if desc in self.tickers:
            del self.tickers[desc]


gstate: GlobalState = GlobalState()
