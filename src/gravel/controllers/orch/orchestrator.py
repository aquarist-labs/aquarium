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
