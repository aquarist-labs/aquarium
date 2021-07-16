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
from typing import Dict, List
from fastapi.logger import logger as fastapi_logger
from pydantic import Field, BaseModel

from gravel.controllers.gstate import Ticker
from gravel.controllers.nodes.mgr import NodeMgr
from gravel.controllers.orch.ceph import Mgr, Mon
from gravel.cephadm.models import VolumeDeviceModel
from gravel.controllers.orch.models import (
    CephOSDDFModel,
    OrchDevicesPerHostModel,
)
from gravel.controllers.orch.orchestrator import Orchestrator


logger: Logger = fastapi_logger


class DeviceUtilizationModel(BaseModel):
    total_kb: int = Field(0, title="Device's total size (KB)")
    avail_kb: int = Field(0, title="Device's available size (KB)")
    used_kb: int = Field(0, title="Device's used size (KB)")
    utilization: float = Field(0, title="Device's utilization")


class DeviceModel(BaseModel):
    host: str
    osd_id: int
    path: str
    rotational: bool
    vendor: str
    model: str
    utilization: DeviceUtilizationModel = Field(DeviceUtilizationModel())


class DeviceHostModel(BaseModel):
    utilization: DeviceUtilizationModel = Field(
        DeviceUtilizationModel(), title="Host's utilization"
    )
    devices: List[DeviceModel] = Field([], title="Host's devices")


class Devices(Ticker):

    _osds_per_host: Dict[str, List[int]] = {}
    _osd_entries: Dict[int, DeviceModel] = {}

    def __init__(
        self,
        probe_interval: float,
        nodemgr: NodeMgr,
        ceph_mgr: Mgr,
        ceph_mon: Mon,
    ):
        super().__init__(probe_interval)
        self.nodemgr = nodemgr
        self.ceph_mon = ceph_mon
        self.ceph_mgr = ceph_mgr

    async def _do_tick(self) -> None:
        await self.probe()

    async def _should_tick(self) -> bool:
        return (
            self.nodemgr.deployment_state.deployed
            or self.nodemgr.deployment_state.ready
        ) and self.nodemgr.started

    async def probe(self) -> None:

        logger.debug("probe devices")

        orch: Orchestrator = Orchestrator(self.ceph_mgr)
        mon: Mon = self.ceph_mon
        device_lst: List[OrchDevicesPerHostModel] = orch.devices_ls()
        osd_df: CephOSDDFModel = mon.osd_df()

        if len(device_lst) == 0 or len(osd_df.nodes) == 0:
            logger.debug("probe > no devices to probe")
            return

        osds_per_host: Dict[str, List[int]] = {}
        osd_entries: Dict[int, DeviceModel] = {}
        for hostdevs in device_lst:
            host: str = hostdevs.name
            devs: List[VolumeDeviceModel] = hostdevs.devices

            osds: List[int] = []
            for dev in devs:
                if dev.available or len(dev.lvs) == 0:
                    continue

                for lv in dev.lvs:
                    if not lv.osd_id:
                        # not a ceph lv
                        continue

                    osd_entries[lv.osd_id] = DeviceModel(
                        host=host,
                        osd_id=lv.osd_id,
                        path=dev.path,
                        rotational=dev.sys_api.rotational,
                        vendor=dev.sys_api.vendor,
                        model=dev.sys_api.model,
                    )
                    osds.append(lv.osd_id)

            osds_per_host[host] = osds

        for osd in osd_df.nodes:
            if osd.id not in osd_entries:
                continue

            osd_entries[osd.id].utilization = DeviceUtilizationModel(
                total_kb=osd.kb,
                avail_kb=osd.kb_avail,
                used_kb=osd.kb_used,
                utilization=osd.utilization,
            )

        self._osds_per_host = osds_per_host
        self._osd_entries = osd_entries

    @property
    def devices_per_host(self) -> Dict[str, DeviceHostModel]:
        devs_per_host: Dict[str, DeviceHostModel] = {}

        for host, osdid_lst in self._osds_per_host.items():

            total_kb: int = 0
            avail_kb: int = 0
            used_kb: int = 0
            raw_utilization: float = 0.0
            devices: List[DeviceModel] = []

            for osdid in osdid_lst:
                assert osdid in self._osd_entries
                device_entry: DeviceModel = self._osd_entries[osdid]
                total_kb += device_entry.utilization.total_kb
                avail_kb += device_entry.utilization.avail_kb
                used_kb += device_entry.utilization.used_kb
                raw_utilization += device_entry.utilization.utilization

                devices.append(self._osd_entries[osdid])

            utilization = 0.0
            if len(devices) > 0:
                utilization = raw_utilization / len(devices)

            host_utilization = DeviceUtilizationModel(
                total_kb=total_kb,
                avail_kb=avail_kb,
                used_kb=used_kb,
                utilization=utilization,
            )
            host_entry = DeviceHostModel(
                utilization=host_utilization, devices=devices
            )
            devs_per_host[host] = host_entry

        return devs_per_host
