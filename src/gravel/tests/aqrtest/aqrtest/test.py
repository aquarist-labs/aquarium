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
from abc import ABC, abstractmethod
from typing import (
    Any,
    Awaitable,
    Callable,
    List,
    Tuple
)
import traceback
import inspect
from aiohttp import ClientSession

import uvicorn  # pyright: reportMissingTypeStubs=false
from fastapi import Request
import aquarium


class AqrTest(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def run_test(self) -> bool:
        return False

    async def run(self) -> Tuple[bool, List[str]]:
        app = aquarium.app_factory()
        started = False
        config = uvicorn.Config(app, host="0.0.0.0", port=1337)
        server = uvicorn.Server(config)
        failures: List[str] = []

        async def run_app() -> None:
            try:
                config.setup_event_loop()
                nonlocal started
                started = True
                await server.serve()
            except Exception:
                print("oops!")
            except asyncio.CancelledError:
                print("cancelled")

        def handle_exception(req: Request, e: Exception) -> None:
            try:
                raise e
            except Exception:
                nonlocal failures
                failures.append(traceback.format_exc())
            stop_app()

        def stop_app() -> None:
            server.should_exit = True
            server.force_exit = True

        app.add_exception_handler(
            Exception, handle_exception
        )  # pyright: reportUnknownMemberType=false
        app.state.api.add_exception_handler(
            Exception, handle_exception
        )  # pyright: reportUnknownMemberType=false

        loop = asyncio.get_event_loop()
        task = loop.create_task(run_app())
        while not started:
            await asyncio.sleep(1)
        await asyncio.sleep(1)
        try:
            res = await asyncio.wait_for(self.run_test(), 300)
        except TimeoutError:
            res = False
            failures.append("test timed out")

        stop_app()
        try:
            await asyncio.wait_for(task, 10)
            print("success waiting for server to stop")
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            print("timed out waiting for server to stop")

        return res, failures


testlist: List[Tuple[str, AqrTest]] = []


def test(name: str):

    def _wrapper(testcls: Any):

        wrapped_class = None
        if inspect.isclass(testcls):
            wrapped_class = testcls
        elif inspect.iscoroutinefunction(testcls):
            class Wrapper(AqrTest):
                async def run_test(self):
                    return await testcls()
            wrapped_class = Wrapper
        else:
            raise TypeError("test must be class or coroutine function")

        testlist.append((name, wrapped_class()))

    return _wrapper


def httptest(func: Callable[[ClientSession], Awaitable[bool]]):

    async def _wrapper(*args: Any, **kwargs: Any) -> bool:
        async with ClientSession() as session:
            return await func(session, *args, **kwargs)
    return _wrapper
