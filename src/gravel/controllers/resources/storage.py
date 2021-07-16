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

from logging import Logger
from typing import Dict
from fastapi.logger import logger as fastapi_logger
from pydantic.fields import Field
from pydantic.main import BaseModel
from gravel.controllers.gstate import Ticker
from gravel.controllers.nodes.mgr import NodeMgr
from gravel.controllers.orch.ceph import Mon


logger: Logger = fastapi_logger


class StorageError(Exception):
    pass


class StorageStatsModel(BaseModel):
    total: int = Field(0, title="Total bytes")
    available: int = Field(0, title="Total bytes available")
    used: int = Field(0, title="Total bytes used")
    raw_used: int = Field(0, title="Total raw bytes used")
    raw_used_ratio: float = Field(0.0, title="Raw used ratio")


class StoragePoolStatsModel(BaseModel):
    used: int = Field(0, title="Pool's bytes used")
    percent_used: float = Field(0, title="Percent used by pool")
    max_available: int = Field(0, title="Maximum bytes available for pool")


class StoragePoolModel(BaseModel):
    id: int = Field(title="Pool ID")
    name: str = Field(title="Pool name")
    stats: StoragePoolStatsModel = Field(title="Pool statistics")


class StorageModel(BaseModel):
    stats: StorageStatsModel = Field(StorageStatsModel(), title="statistics")
    pools_by_id: Dict[int, StoragePoolModel] = Field({}, title="Pool by ID")
    pools_by_name: Dict[str, StoragePoolModel] = Field({}, title="Pool by name")


class Storage(Ticker):
    def __init__(self, probe_interval: float, nodemgr: NodeMgr, ceph_mon: Mon):
        super().__init__(probe_interval)
        self.nodemgr: NodeMgr = nodemgr
        self.ceph_mon: Mon = ceph_mon
        self._state: StorageModel = StorageModel()

    async def _do_tick(self) -> None:
        await self._update()

    async def _should_tick(self) -> bool:
        return (
            self.nodemgr.deployment_state.deployed
            or self.nodemgr.deployment_state.ready
        ) and self.nodemgr.started

    @property
    def available(self) -> int:
        return self._state.stats.available

    @property
    def used(self) -> int:
        return self._state.stats.used

    @property
    def total(self) -> int:
        return self._state.stats.total

    def usage(self) -> StorageModel:
        return self._state

    async def _update(self) -> None:
        try:
            mon = self.ceph_mon
            df = mon.df()
        except Exception as e:
            raise StorageError("error obtaining info from cluster") from e

        self._state.stats = StorageStatsModel(
            total=df.stats.total_bytes,
            available=df.stats.total_avail_bytes,
            used=df.stats.total_used_bytes,
            raw_used=df.stats.total_used_raw_bytes,
            raw_used_ratio=df.stats.total_used_raw_ratio,
        )
        by_id: Dict[int, StoragePoolModel] = {}
        by_name: Dict[str, StoragePoolModel] = {}
        for p in df.pools:
            pool: StoragePoolModel = StoragePoolModel(
                id=p.id,
                name=p.name,
                stats=StoragePoolStatsModel(
                    used=p.stats.bytes_used,
                    percent_used=p.stats.percent_used,
                    max_available=p.stats.max_avail,
                ),
            )
            by_id[p.id] = pool
            by_name[p.name] = pool
        self._state.pools_by_name = by_name
        self._state.pools_by_id = by_id
