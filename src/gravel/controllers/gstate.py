
import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Callable, Any

from gravel.controllers.config import Config


class GlobalState:

    executor: ThreadPoolExecutor
    counter: int
    config: Config

    def __init__(self):
        self.executor = ThreadPoolExecutor()
        self.counter = 0
        self.config = Config()
        pass

    async def run_in_background(self, func: Callable, *args: Any):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(self.executor, func, *args)


