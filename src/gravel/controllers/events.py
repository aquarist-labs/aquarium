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

from enum import Enum
from logging import Logger
from typing import Dict, List, Optional
from datetime import datetime as dt
from fastapi.logger import logger as fastapi_logger
from pydantic import (
    BaseModel,
    Field
)

from gravel.controllers.nodes.mgr import (
    NodeMgr,
    NodeStageEnum,
    get_node_mgr
)
from gravel.controllers.gstate import (
    gstate,
    Ticker
)


logger: Logger = fastapi_logger


class EventSeverityEnum(int, Enum):
    NONE = 0
    INFO = 1
    WARN = 2
    ERROR = 3


class EventMessageModel(BaseModel):
    timestamp: Optional[dt] = Field(None, title="event's timestamp")
    severity: EventSeverityEnum = Field(EventSeverityEnum.NONE,
                                        title="event's severity")
    message: str = Field("", title="event's message")


class Events(Ticker):

    _events: List[EventMessageModel]
    _events_by_msg: Dict[str, EventMessageModel]

    def __init__(self):
        super().__init__(
            "events",
            gstate.config.options.events.tick_interval
        )
        self._events = []
        self._events_by_msg = {}

    async def _do_tick(self) -> None:

        def _should_drop(item: EventMessageModel) -> bool:
            assert item.timestamp
            now: dt = dt.now()
            diff = now - item.timestamp
            return diff.total_seconds() >= gstate.config.options.events.ttl

        if len(self._events) == 0:
            return
        while True:
            first: EventMessageModel = self._events[0]
            if _should_drop(first):
                self._events.pop(0)
            else:
                break

    async def _should_tick(self) -> bool:
        nodemgr: NodeMgr = get_node_mgr()
        return nodemgr.stage >= NodeStageEnum.BOOTSTRAPPED

    async def add(self, msg: str, severity: EventSeverityEnum) -> None:

        event: Optional[EventMessageModel] = self._events_by_msg.get(msg)
        if event:
            self._events.remove(event)
            event.timestamp = dt.now()
            self._events.append(event)
            return

        if len(self._events) >= gstate.config.options.events.queue_max:
            event = self._events.pop(0)
            del self._events_by_msg[event.message]

        event = EventMessageModel(
            timestamp=dt.now(),
            severity=severity,
            message=msg
        )

        self._events.append(event)
        self._events_by_msg[msg] = event

    @property
    def events(self) -> List[EventMessageModel]:
        lst: List[EventMessageModel] = self._events.copy()
        lst.reverse()
        return lst


_events = Events()


def get_events_ctrl() -> Events:
    global _events
    return _events
