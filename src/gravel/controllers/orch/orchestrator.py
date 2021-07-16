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
from typing import Any, Dict, List, Optional
import yaml

from logging import Logger
from fastapi.logger import logger as fastapi_logger
from pydantic.tools import parse_obj_as
from gravel.controllers.orch.ceph import CephCommandError, Mgr
from gravel.controllers.orch.models import (
    OrchDevicesPerHostModel,
    OrchHostListModel,
)


logger: Logger = fastapi_logger


class Orchestrator:

    cluster: Mgr

    def __init__(self, ceph_mgr: Mgr):
        self.cluster = ceph_mgr

    def call(self, cmd: Dict[str, Any], inbuf: bytes = b"") -> Any:
        if "format" not in cmd:
            cmd["format"] = "json"
        return self.cluster.call(cmd, inbuf=inbuf)

    def host_ls(self) -> List[OrchHostListModel]:
        cmd = {"prefix": "orch host ls"}
        res = self.call(cmd)
        return parse_obj_as(List[OrchHostListModel], res)

    def host_exists(self, hostname: str) -> bool:
        hosts: List[OrchHostListModel] = self.host_ls()
        for h in hosts:
            if h.hostname == hostname:
                return True
        return False

    async def wait_host_added(self, hostname: str) -> None:
        while not self.host_exists(hostname):
            await asyncio.sleep(1.0)

    def devices_ls(
        self, hostname: Optional[str] = None
    ) -> List[OrchDevicesPerHostModel]:
        cmd: Dict[str, Any] = {"prefix": "orch device ls"}
        if hostname and len(hostname) > 0:
            cmd["hostname"] = [hostname]

        res = self.call(cmd)
        return parse_obj_as(List[OrchDevicesPerHostModel], res)

    def assimilate_devices(self, host: str, devices: List[str]) -> None:
        spec = {
            "service_type": "osd",
            "service_id": "default_drive_group",
            "placement": {"hosts": [host]},
            "data_devices": {"paths": devices},
        }
        specstr: Optional[str] = yaml.dump(spec)  # type: ignore
        assert specstr is not None
        specbuf: bytes = specstr.encode("utf-8")
        cmd = {"prefix": "orch apply osd"}
        res = self.call(cmd, inbuf=specbuf)
        assert "result" in res

    def devices_assimilated(self, hostname: str, devs: List[str]) -> bool:
        assert len(devs) > 0
        assert hostname and len(hostname) > 0

        res = self.devices_ls(hostname)
        logger.debug(f"devices ls: {res}")
        if len(res) == 0:
            return False

        assert len(res) == 1
        entry: OrchDevicesPerHostModel = res[0]
        assert entry.name == hostname

        if len(entry.devices) == 0:
            logger.debug("devices not yet probed on host, must wait")
            return False

        hostdevs: Dict[str, bool] = {}
        for dev in entry.devices:
            hostdevs[dev.path] = dev.available
        for dev in devs:
            assert dev in hostdevs
            if hostdevs[dev]:
                # if available, not yet assimilated
                return False
        return True

    def apply_mds(self, fsname: str) -> None:
        cmd = {"prefix": "orch apply mds", "fs_name": fsname}
        self.call(cmd)

    def get_public_key(self) -> str:
        cmd = {"prefix": "cephadm get-pub-key"}
        res = self.call(cmd)
        assert "result" in res
        return res["result"]

    def host_add(self, hostname: str, address: str) -> bool:
        assert hostname
        assert address

        cmd = {"prefix": "orch host add", "hostname": hostname, "addr": address}
        try:
            self.call(cmd)
        except CephCommandError:
            logger.error(f"host add > unable to add {hostname} {address}")
            return False
        return True
