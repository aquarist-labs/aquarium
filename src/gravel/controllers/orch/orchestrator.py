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

from typing import Any, Dict, List

from logging import Logger
from fastapi.logger import logger as fastapi_logger
from pydantic.tools import parse_obj_as
from gravel.controllers.orch.ceph import (
    CephCommandError,
    Mgr
)
from gravel.controllers.orch.models import (
    OrchDevicesPerHostModel,
    OrchHostListModel
)


logger: Logger = fastapi_logger


class Orchestrator:

    cluster: Mgr

    def __init__(self):
        self.cluster = Mgr()

    def call(self, cmd: Dict[str, Any]) -> Any:
        if "format" not in cmd:
            cmd["format"] = "json"
        return self.cluster.call(cmd)

    def host_ls(self) -> List[OrchHostListModel]:
        cmd = {"prefix": "orch host ls"}
        res = self.call(cmd)
        return parse_obj_as(List[OrchHostListModel], res)

    def devices_ls(self) -> List[OrchDevicesPerHostModel]:
        cmd = {"prefix": "orch device ls"}
        res = self.call(cmd)
        return parse_obj_as(List[OrchDevicesPerHostModel], res)

    def assimilate_all_devices(self) -> None:
        cmd = {
            "prefix": "orch apply osd",
            "all_available_devices": True
        }
        res = self.call(cmd)
        assert "result" in res

    def all_devices_assimilated(self) -> bool:
        res = self.devices_ls()
        for host in res:
            for dev in host.devices:
                if dev.available:
                    return False
        return True

    def apply_mds(self, fsname: str) -> None:
        cmd = {
            "prefix": "orch apply mds",
            "fs_name": fsname
        }
        self.call(cmd)

    def get_public_key(self) -> str:
        cmd = {
            "prefix": "cephadm get-pub-key"
        }
        res = self.call(cmd)
        assert "result" in res
        return res["result"]

    def host_add(self, hostname: str, address: str) -> bool:
        assert hostname
        assert address

        cmd = {
            "prefix": "orch host add",
            "hostname": hostname,
            "addr": address
        }
        try:
            self.call(cmd)
        except CephCommandError:
            logger.error(
                f"=> orch -- host add > unable to add {hostname} {address}"
            )
            return False
        return True
