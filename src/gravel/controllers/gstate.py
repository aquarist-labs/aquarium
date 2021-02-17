# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import asyncio
from abc import ABC, abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor
from logging import Logger
from typing import Callable, Any, Dict
from fastapi.logger import logger as fastapi_logger

from gravel.controllers.config import Config


logger: Logger = fastapi_logger


class Ticker(ABC):
    @abstractmethod
    async def tick(self) -> None:
        pass


class GlobalState:

    executor: ThreadPoolExecutor
    counter: int
    config: Config
    is_shutting_down: bool
    tickers: Dict[str, Ticker]

    def __init__(self):
        self.executor = ThreadPoolExecutor()
        self.counter = 0
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
            logger.debug("=> tick")
            await asyncio.sleep(1)

            for desc, ticker in self.tickers.items():
                logger.debug(f"=> tick {desc}")
                asyncio.create_task(ticker.tick())

        logger.info("=> tick shutting down")

    def add_ticker(self, desc: str, whom: Ticker) -> None:
        if desc not in self.tickers:
            self.tickers[desc] = whom

    def rm_ticker(self, desc: str) -> None:
        if desc in self.tickers:
            del self.tickers[desc]


gstate: GlobalState = GlobalState()
