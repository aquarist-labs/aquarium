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
from typing import Tuple, Optional, Any, cast
from logging import Logger

import websockets
from fastapi import status
from fastapi.logger import logger as fastapi_logger
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket

from gravel.controllers.nodes.messages import MessageModel


class ConnectionError(Exception):
    pass


class ConnectionManagerNotStarted(ConnectionError):
    pass


logger: Logger = fastapi_logger


class ConnMgr:

    _is_incoming_started: bool
    _incoming_queue: asyncio.Queue[Tuple[IncomingConnection, MessageModel]]

    def __init__(self):
        self._is_incoming_started = False
        self._incoming_queue = asyncio.Queue()

    def start_receiving(self) -> None:
        self._is_incoming_started = True

    def is_started(self) -> bool:
        return self._is_incoming_started

    async def on_incoming_receive(
        self, conn: IncomingConnection, msg: MessageModel
    ) -> None:
        logger.debug(f"connmgr -- incoming recv: {conn}, {msg}")

        if not self.is_started():
            raise ConnectionManagerNotStarted()

        await self._incoming_queue.put((conn, msg))
        logger.debug(f"connmgr -- queue len: {self._incoming_queue.qsize()}")

    async def wait_incoming_msg(
        self,
    ) -> Tuple[IncomingConnection, MessageModel]:
        return await self._incoming_queue.get()

    async def connect(self, endpoint: str) -> OutgoingConnection:
        wsclient = await websockets.connect(endpoint)
        conn = OutgoingConnection(wsclient)
        return conn


class IncomingConnection(WebSocketEndpoint):

    _ws: Optional[WebSocket] = None

    async def on_connect(self, websocket: WebSocket) -> None:
        logger.debug(f"incoming -- from {websocket.client}")

        connmgr: ConnMgr = get_conn_mgr()
        if not connmgr.is_started():
            await websocket.close(status.WS_1013_TRY_AGAIN_LATER)
            return

        self._ws = websocket
        await websocket.accept()

    async def on_disconnect(
        self, websocket: WebSocket, close_code: int
    ) -> None:
        logger.debug(f"incoming -- disconnect from {websocket.client}")
        self._ws = None

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        logger.debug(f"incoming -- recv from {websocket.client}: {data}")
        connmgr: ConnMgr = get_conn_mgr()
        assert connmgr.is_started()
        msg: MessageModel = MessageModel.parse_raw(data)
        await connmgr.on_incoming_receive(self, msg)

    async def send_msg(self, data: MessageModel) -> None:
        logger.debug(f"incoming -- send to {self._ws} data {data}")
        assert self._ws
        await self._ws.send_text(data.json())

    @property
    def address(self) -> str:
        assert self._ws
        return cast(
            str, self._ws.client.host
        )  # pyright: reportUnknownMemberType=false


class OutgoingConnection:
    _ws: websockets.WebSocketClientProtocol

    def __init__(self, ws: websockets.WebSocketClientProtocol) -> None:
        self._ws = ws

    async def send(self, msg: MessageModel) -> None:
        assert self._ws
        await self._ws.send(msg.json())

    async def receive(self) -> MessageModel:
        assert self._ws
        raw = await self._ws.recv()
        return MessageModel.parse_raw(raw)

    async def close(self) -> None:
        assert self._ws
        await self._ws.close()


_connmgr = ConnMgr()


def get_conn_mgr() -> ConnMgr:
    return _connmgr
