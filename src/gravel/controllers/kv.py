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
from typing import Callable, Optional, List
import aetcd3
import aetcd3.locks
import aetcd3.events
import grpclib.exceptions

from logging import Logger
from fastapi.logger import logger as fastapi_logger

logger: Logger = fastapi_logger


class Lock:
    _lock: aetcd3.locks.Lock
    _is_acquired: bool

    def __init__(self, lock: aetcd3.locks.Lock):
        self._lock = lock
        self._is_acquired = False

    async def acquire(self) -> None:
        await self._lock.acquire()
        self._is_acquired = True

    async def release(self) -> None:
        if not self._is_acquired:
            return
        await self._lock.release()
        self._is_acquired = False


class KV:

    _client: Optional[aetcd3.Etcd3Client]
    _is_open: bool
    _is_closing: bool

    def __init__(self):
        self._client = None
        self._is_open = False
        self._is_closing = False

    async def ensure_connection(self) -> None:
        """Open k/v store connection"""
        # try getting the status, loop until we make it.
        opened = False
        while not self._is_closing:
            try:
                async with aetcd3.client() as client:
                    await client.status()
            except Exception:
                logger.warn("etcd not up yet? sleep.")
                await asyncio.sleep(1.0)
                continue
            opened = True
            break
        if opened:
            self._client = aetcd3.client()
            self._is_open = True
            logger.info("opened kvstore connection")

    async def close(self) -> None:
        """Close k/v store connection"""
        self._is_closing = True
        if not self._client:
            self._is_open = False
            return
        await self._client.close()
        self._client = None
        self._is_open = False

    async def put(self, key: str, value: str) -> None:
        """Put key/value pair"""
        assert self._client
        await self._client.put(key, value)

    async def get(self, key: str) -> Optional[str]:
        """Get value for provided key"""
        assert self._client
        value, _ = await self._client.get(key)
        if not value:
            return None
        return value.decode("utf-8")

    async def get_prefix(self, key: str) -> List[str]:
        """Get a range of keys with a prefix"""
        assert self._client
        values = []
        async for value, _ in self._client.get_prefix(key):  # type: ignore[attr-defined]
            values.append(value.decode("utf-8"))
        return values

    async def rm(self, key: str) -> None:
        """Remove key from store"""
        assert self._client
        await self._client.delete(key)

    async def lock(self, key: str) -> Lock:
        """Lock a given key. Requires compliant consumers."""
        assert self._client
        return Lock(self._client.lock(key))

    async def watch(
        self, key: str, callback: Callable[[str, str], None]
    ) -> int:
        """Watch updates on a given key"""
        assert self._client

        async def _cb(what: aetcd3.events.Event) -> None:
            if (
                not what
                or type(what) == grpclib.exceptions.StreamTerminatedError
            ):
                return
            callback(what.key.decode("utf-8"), what.value.decode("utf-8"))

        return await self._client.add_watch_callback(key, _cb)

    async def cancel_watch(self, watch_id: int) -> None:
        """Cancel a watch"""
        assert self._client
        await self._client.cancel_watch(watch_id)
