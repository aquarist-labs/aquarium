# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from typing import Any, Dict, List

from pydantic.tools import parse_obj_as
from gravel.controllers.orch.ceph import Mgr
from gravel.controllers.orch.models \
    import OrchDevicesPerHostModel, OrchHostListModel


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
