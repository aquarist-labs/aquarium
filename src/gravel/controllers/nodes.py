# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from __future__ import annotations
import asyncio
from enum import Enum
from logging import Logger
from typing import (
    Any,
    Dict,
    List,
    Optional, Tuple,
    Union,
    cast
)
from uuid import UUID, uuid4
from pathlib import Path
from datetime import datetime as dt
import websockets

from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket
from gravel.controllers.config import DeploymentStage

from gravel.controllers.gstate import gstate


logger: Logger = fastapi_logger


class MessageTypeEnum(int, Enum):
    JOIN = 1
    WELCOME = 2


class NodeOpType(int, Enum):
    NONE = 0
    JOIN = 1


class MessageModel(BaseModel):
    type: MessageTypeEnum
    data: Any


class JoinMessageModel(BaseModel):
    uuid: UUID
    token: str


class Peer:
    endpoint: str
    conn: Union[IncomingConnection, OutgoingConnection]

    def __init__(self, endpoint: str, conn: Union[IncomingConnection, OutgoingConnection]):
        self.endpoint = endpoint
        self.conn = conn


class NodeRoleEnum(int, Enum):
    NONE = 0
    LEADER = 1
    FOLLOWER = 2


class NodeStateModel(BaseModel):
    uuid: UUID
    role: NodeRoleEnum


class ManifestModel(BaseModel):
    aquarium_uuid: UUID
    version: int
    modified: dt
    nodes: List[NodeStateModel]


class ConnMgr:

    _conns: List[Peer]
    _conn_by_endpoint: Dict[str, Peer]

    _passive_conns: List[Peer]
    _active_conns: List[Peer]

    _incoming_queue: asyncio.Queue[Tuple[IncomingConnection, MessageModel]]

    def __init__(self):
        self._conns = []
        self._passive_conns = []
        self._active_conns = []
        self._conn_by_endpoint = {}
        self._incoming_queue = asyncio.Queue()

    def register_connect(
        self,
        endpoint: str,
        conn: Union[OutgoingConnection, IncomingConnection],
        is_passive: bool
    ) -> None:
        peer = Peer(endpoint=endpoint, conn=conn)
        self._conns.append(peer)
        self._conn_by_endpoint[endpoint] = peer

        if is_passive:
            self._passive_conns.append(peer)
        else:
            self._active_conns.append(peer)

    async def on_incoming_receive(
        self,
        conn: IncomingConnection,
        msg: MessageModel
    ) -> None:
        logger.debug(f"=> connmgr -- incoming recv: {conn}, {msg}")
        await self._incoming_queue.put((conn, msg))
        logger.debug(f"=> connmgr -- queue len: {self._incoming_queue.qsize()}")

    async def wait_incoming_msg(
        self
    ) -> Tuple[IncomingConnection, MessageModel]:
        return await self._incoming_queue.get()

    async def connect(self, endpoint: str) -> OutgoingConnection:

        if endpoint in self._conn_by_endpoint:
            conn = self._conn_by_endpoint[endpoint].conn
            return cast(OutgoingConnection, conn)

        wsclient = await websockets.connect(endpoint)
        conn = OutgoingConnection(wsclient)
        self.register_connect(endpoint, conn, is_passive=False)
        return conn


class Mgr:

    _connmgr: ConnMgr
    _incoming_task: asyncio.Task
    _shutting_down: bool
    _state: Optional[NodeStateModel]
    _manifest: Optional[ManifestModel]

    def __init__(self):
        self._connmgr = ConnMgr()
        self._shutting_down = False
        self._state = self._load_state()
        self._manifest = self._load_manifest()

        assert (self._state and self._manifest) or \
               (not self._state and not self._manifest)

        self._incoming_task = asyncio.create_task(self._incoming_msg_task())

    async def join(self, address: str, token: str) -> bool:
        logger.debug(f"=> mgr -- join > with addr {address}, token: {token}")
        uri: str = f"ws://{address}/api/nodes/ws"
        conn = await self._connmgr.connect(uri)
        logger.debug(f"=> mgr -- join > conn: {conn}")

        uuid: UUID = uuid4()
        joinmsg = JoinMessageModel(uuid=uuid, token=token)
        msg = MessageModel(type=MessageTypeEnum.JOIN, data=joinmsg.dict())
        await conn.send(msg)
        reply: MessageModel = await conn.receive()
        logger.debug(f"=> mgr -- join > recv: {reply}")
        return True

    async def finish_bootstrap(self):
        assert not self._state
        confdir: Path = gstate.config.confdir
        assert confdir.exists()
        assert confdir.is_dir()
        statefile: Path = confdir.joinpath("node.json")
        assert not statefile.exists()
        manifestfile: Path = confdir.joinpath("manifest.json")
        assert not manifestfile.exists()

        nodestate: NodeStateModel = NodeStateModel(
            uuid=uuid4(),
            role=NodeRoleEnum.LEADER
        )
        statefile.write_text(nodestate.json())

        manifest: ManifestModel = ManifestModel(
            aquarium_uuid=uuid4(),
            version=1,
            modified=dt.now(),
            nodes=[nodestate]
        )
        manifestfile.write_text(manifest.json())

    @property
    def connmgr(self) -> ConnMgr:
        return self._connmgr

    def _load_state(self) -> Optional[NodeStateModel]:
        confdir: Path = gstate.config.confdir
        assert confdir.exists()
        assert confdir.is_dir()
        statefile: Path = confdir.joinpath("node.json")
        if not statefile.exists():
            stage = gstate.config.deployment_state.stage
            assert stage < DeploymentStage.bootstrapped
            return None
        return NodeStateModel.parse_file(statefile)

    def _load_manifest(self) -> Optional[ManifestModel]:
        confdir: Path = gstate.config.confdir
        assert confdir.exists()
        assert confdir.is_dir()
        manifestfile: Path = confdir.joinpath("manifest.json")
        if not manifestfile.exists():
            stage = gstate.config.deployment_state.stage
            assert stage < DeploymentStage.bootstrapped
            return None
        return ManifestModel.parse_file(manifestfile)

    async def _incoming_msg_task(self) -> None:
        while not self._shutting_down:
            logger.debug("=> mgr -- incoming msg task > wait")
            conn, msg = await self._connmgr.wait_incoming_msg()
            logger.debug(f"=> mgr -- incoming msg task > {conn}, {msg}")
            await self._handle_incoming_msg(conn, msg)
            logger.debug("=> mgr -- incoming msg task > handled")

    async def _handle_incoming_msg(
        self,
        conn: IncomingConnection,
        msg: MessageModel
    ) -> None:
        logger.debug(f"=> mgr -- handle msg > type: {msg.type}")
        if msg.type == MessageTypeEnum.JOIN:
            logger.debug("=> mgr -- handle msg > join")
            await conn.send_msg(
                MessageModel(type=MessageTypeEnum.WELCOME, data={})
            )
            logger.debug("=> mgr -- handle msg > sent welcome")
        pass


_mgr = Mgr()


def get_node_mgr() -> Mgr:
    return _mgr


def get_conn_mgr() -> ConnMgr:
    return get_node_mgr().connmgr


class IncomingConnection(WebSocketEndpoint):

    _ws: Optional[WebSocket] = None

    async def on_connect(self, websocket: WebSocket) -> None:
        logger.debug(f"=> connection -- from {websocket.client}")
        self._ws = websocket
        host: str = \
            f"{websocket.client.host}"  # pyright: reportUnknownMemberType=false
        port: str = \
            f"{websocket.client.port}"  # pyright: reportUnknownMemberType=false
        endpoint: str = f"{host}:{port}"
        await websocket.accept()
        get_conn_mgr().register_connect(endpoint, self, is_passive=True)

    async def on_disconnect(
        self,
        websocket: WebSocket,
        close_code: int
    ) -> None:
        logger.debug(f"=> connection -- disconnect from {websocket.client}")
        self._ws = None

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        logger.debug(f"=> connection -- recv from {websocket.client}: {data}")
        msg: MessageModel = MessageModel.parse_raw(data)
        await get_conn_mgr().on_incoming_receive(self, msg)

    async def send_msg(self, data: MessageModel) -> None:
        logger.debug(f"=> connection -- send to {self._ws} data {data}")
        assert self._ws
        await self._ws.send_text(data.json())


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
