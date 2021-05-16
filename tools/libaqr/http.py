# project aquarium's testing battery
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

from typing import Any
import aiohttp
from contextlib import asynccontextmanager


class HTTPSession:
    _session: aiohttp.ClientSession
    _port: int
    _url: str

    def __init__(self, session: aiohttp.ClientSession, port: int) -> None:
        self._session = session
        self._port = port
        self._url = f"http://127.0.0.1:{self._port}"

    async def get(
        self,
        what: str,
        *args: Any,
        **kwargs: Any
    ) -> aiohttp.ClientResponse:
        sep = "" if what.startswith("/") else "/"
        endpoint = f"{self._url}{sep}{what}"
        return await self._session.get(endpoint, *args, **kwargs)

    async def post(
        self,
        what: str,
        *args: Any,
        **kwargs: Any
    ) -> aiohttp.ClientResponse:
        sep = "" if what.startswith("/") else "/"
        endpoint = f"{self._url}{sep}{what}"
        return await self._session.post(endpoint, *args, **kwargs)


@asynccontextmanager
async def conn(port: int = 1337):
    clientsession = None
    try:
        clientsession = aiohttp.ClientSession()
        httpsession = HTTPSession(clientsession, port)
        yield httpsession
    finally:
        if clientsession:
            await clientsession.close()
