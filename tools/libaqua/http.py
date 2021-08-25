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

from typing import Any, Optional
import aiohttp
from contextlib import asynccontextmanager


class HTTPSession:
    _session: aiohttp.ClientSession
    _port: int
    _url: str
    _access_token: Optional[str]

    def __init__(self, session: aiohttp.ClientSession, port: int) -> None:
        self._session = session
        self._port = port
        self._url = f"http://127.0.0.1:{self._port}"
        self._access_token = None

    async def get(
        self,
        what: str,
        *args: Any,
        **kwargs: Any
    ) -> aiohttp.ClientResponse:
        sep = "" if what.startswith("/") else "/"
        endpoint = f"{self._url}{sep}{what}"
        headers = {}
        self._update_headers(headers)
        return await self._session.get(endpoint, headers=headers,
                                       *args, **kwargs)

    async def post(
        self,
        what: str,
        *args: Any,
        **kwargs: Any
    ) -> aiohttp.ClientResponse:
        sep = "" if what.startswith("/") else "/"
        endpoint = f"{self._url}{sep}{what}"
        headers = {}
        self._update_headers(headers)
        return await self._session.post(endpoint, headers=headers,
                                        *args, **kwargs)

    async def login(self, username: str, password: str):
        print(f">>> Logging in (username={username}, password={password}) ...")
        try:
            auth = aiohttp.BasicAuth(username, password)
            form_data = aiohttp.FormData()
            form_data.add_field("username", username)
            form_data.add_field("password", password)
            form_data.add_field("grant_type", "password")
            res = await self._session.post(f"{self._url}/auth/login",
                                           auth=auth,
                                           data=form_data)
            assert res.status == 200
            self._access_token = res.json()["access_token"]
        except Exception as e:
            print(f">>> Failed to log in")
            raise e

    async def logout(self):
        print(">>> Logging out ...")
        res = await self.post("/auth/logout")
        assert res.status == 200
        self._access_token = None

    def _update_headers(self, headers):
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"


@asynccontextmanager
async def conn(port: int = 1337, login=False, username="admin", password="aquarium"):
    clientsession = None
    try:
        clientsession = aiohttp.ClientSession()
        httpsession = HTTPSession(clientsession, port)
        if login:
            await httpsession.login(username, password)
        yield httpsession
    finally:
        if httpsession and login:
            await httpsession.logout()
        if clientsession:
            await clientsession.close()
