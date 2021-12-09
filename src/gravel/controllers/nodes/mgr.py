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
from enum import Enum
from logging import Logger
from typing import Optional
from uuid import UUID, uuid4

from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel

from gravel.controllers.gstate import GlobalState
from gravel.controllers.inventory.nodeinfo import NodeInfoModel
from gravel.controllers.inventory.subscriber import Subscriber
from gravel.controllers.nodes.errors import (
    NodeError,
    NodeNetworkAddressNotAvailable,
    NodeNotStartedError,
)

logger: Logger = fastapi_logger


#
# INIT STATE MACHINE
# ------------------
#


class NodeInitStage(int, Enum):
    NONE = 0
    INITED = 1
    AVAILABLE = 2
    STOPPING = 3
    STOPPED = 4


class NodeStateModel(BaseModel):
    uuid: UUID
    address: Optional[str]
    hostname: Optional[str]


class NodeMgr:

    _init_stage: NodeInitStage
    _shutting_down: bool
    _state: Optional[NodeStateModel]
    _inventory_sub: Optional[Subscriber]
    _deployed: bool
    _gstate: GlobalState

    def __init__(self, gstate: GlobalState):
        self._init_stage = NodeInitStage.NONE
        self._shutting_down = False
        self._state = None
        self._inventory_sub = None
        self._deployed = False
        self._gstate = gstate

    def init(self) -> None:
        logger.debug("Node Manager Init.")
        # attempt reading our node state from disk; create one if not found.
        try:
            self._state = self._gstate.config.read_model("node", NodeStateModel)
        except FileNotFoundError:
            self._state = NodeStateModel(
                uuid=uuid4(), address=None, hostname=None
            )
            try:
                self._gstate.config.write_model("node", self._state)
            except Exception as e:
                raise NodeError(str(e))
        except Exception as e:
            raise NodeError(str(e))
        self._init_stage = NodeInitStage.INITED

    async def start(self) -> None:
        assert self._state
        assert self._init_stage == NodeInitStage.INITED
        logger.debug("Start Node Manager")

        async def _inventory_subscriber(nodeinfo: NodeInfoModel) -> None:
            logger.debug(f"Inventory update from subscription: {nodeinfo}")
            assert nodeinfo
            await self._node_update_info(nodeinfo)
            if self._init_stage == NodeInitStage.INITED:
                logger.debug("Node Manager now AVAILABLE.")
                self._init_stage = NodeInitStage.AVAILABLE

        async def _task() -> None:
            logger.debug("subscribe inventory updates")
            self._inventory_sub = await self._gstate.inventory.subscribe(
                _inventory_subscriber, once=False
            )

        asyncio.create_task(_task())

    def mark_deployed(self) -> None:
        self._deployed = True

    async def shutdown(self) -> None:
        pass

    async def _node_update_info(self, nodeinfo: NodeInfoModel) -> None:

        assert self._state is not None
        self._state.hostname = nodeinfo.hostname

        address: Optional[str] = None
        for nic in nodeinfo.nics.values():
            if nic.iftype == "loopback":
                continue
            address = nic.ipv4_address
            break

        if not address:
            raise NodeNetworkAddressNotAvailable()

        assert address
        netmask_idx = address.find("/")
        if netmask_idx > 0:
            address = address[:netmask_idx]

        self._state.address = address
        await self._save_state()

    def _node_shutdown(self) -> None:
        """shutting down, stop node"""
        self._init_stage = NodeInitStage.STOPPING

    @property
    def inited(self) -> bool:
        return self._init_stage >= NodeInitStage.INITED

    @property
    def available(self) -> bool:
        return self._init_stage >= NodeInitStage.AVAILABLE

    @property
    def ready(self) -> bool:
        return self.available and self._deployed

    @property
    def address(self) -> str:
        assert self._state
        assert self._state.address
        return self._state.address

    @property
    def uuid(self) -> UUID:
        if self._state is None:
            raise NodeNotStartedError()
        return self._state.uuid

    async def _save_state(self) -> None:
        try:
            assert self._state is not None
            self._gstate.config.write_model("node", self._state)
        except Exception as e:
            raise NodeError(str(e))
