
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from logging import Logger
from typing import Callable, Any
from fastapi.logger import logger as fastapi_logger

from gravel.controllers.config import Config


logger: Logger = fastapi_logger


class GlobalState:

    executor: ThreadPoolExecutor
    counter: int
    config: Config
    is_shutting_down: bool

    def __init__(self):
        self.executor = ThreadPoolExecutor()
        self.counter = 0
        self.config = Config()
        self.is_shutting_down = False
        pass

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
            logger.info("=> tick")
            await asyncio.sleep(1)

        logger.info("=> tick shutting down")
