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
from typing import Dict, List, Optional

from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field

from gravel.controllers.gstate import GlobalState, Ticker
from gravel.controllers.nodes.mgr import NodeMgr
from gravel.controllers.orch.ceph import Mon
from gravel.controllers.orch.models import (
    CephOSDPoolStatsModel,
    CephStatusModel,
)

logger: Logger = fastapi_logger


class CephStatusNotAvailableError(Exception):
    pass


class ClientIORateNotAvailableError(Exception):
    pass


class ClientIORateModel(BaseModel):
    read: int = Field(0, title="Client read rate (byte/s)")
    write: int = Field(0, title="Client write rate (byte/s)")
    read_ops: int = Field(0, title="Client read ops rate (ops/s)")
    write_ops: int = Field(0, title="Client write ops rate (ops/s)")


class OverallClientIORateModel(BaseModel):
    cluster: ClientIORateModel = Field(ClientIORateModel(), title="cluster IO")


class Status(Ticker):

    _mon: Optional[Mon]
    _latest_cluster: Optional[CephStatusModel]
    _latest_pools_stats: Dict[int, CephOSDPoolStatsModel]

    def __init__(
        self, probe_interval: float, gstate: GlobalState, nodemgr: NodeMgr
    ):
        super().__init__(probe_interval)
        self.gstate = gstate
        self.nodemgr = nodemgr
        self._mon = gstate.ceph_mon
        self._latest_cluster = None
        self._latest_pools_stats = {}

    async def _do_tick(self) -> None:
        await self.probe()

    async def _should_tick(self) -> bool:
        return (
            self.nodemgr.deployment_state.deployed
            or self.nodemgr.deployment_state.ready
        ) and self.nodemgr.started

    async def probe(self) -> None:
        assert self._mon
        self._latest_cluster = self._mon.status

        pool_stats: List[CephOSDPoolStatsModel] = self._mon.get_pools_stats()
        latest_pool_stats: Dict[int, CephOSDPoolStatsModel] = {}
        for pool in pool_stats:
            latest_pool_stats[pool.pool_id] = pool
        self._latest_pools_stats = latest_pool_stats

    @property
    def status(self) -> CephStatusModel:
        if not self._latest_cluster:
            raise CephStatusNotAvailableError()
        return self._latest_cluster

    @property
    def client_io_rate(self) -> OverallClientIORateModel:

        if len(self._latest_pools_stats) == 0 or not self._latest_cluster:
            raise ClientIORateNotAvailableError()

        cluster_rates: ClientIORateModel = ClientIORateModel(
            read=self._latest_cluster.pgmap.read_bytes_sec,
            write=self._latest_cluster.pgmap.write_bytes_sec,
            read_ops=self._latest_cluster.pgmap.read_op_per_sec,
            write_ops=self._latest_cluster.pgmap.write_op_per_sec,
        )

        return OverallClientIORateModel(cluster=cluster_rates)
