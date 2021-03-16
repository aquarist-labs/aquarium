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

from typing import List

from pydantic.tools import parse_obj_as
from gravel.controllers.orch.ceph import CephCommandError, Mgr, Mon

from gravel.controllers.orch.models \
    import CephFSListEntryModel, CephFSNameModel, CephFSVolumeListModel
from gravel.controllers.orch.orchestrator import Orchestrator


class CephFSError(Exception):
    pass


class CephFS:

    mgr: Mgr
    mon: Mon

    def __init__(self):
        self.mgr = Mgr()
        self.mon = Mon()
        pass

    def create(self, name: str) -> None:

        cmd = {
            "prefix": "fs volume create",
            "name": name
        }
        try:
            # this is expected to be a silent command
            self.mgr.call(cmd)
        except CephCommandError as e:
            raise CephFSError(e) from e

        # schedule orchestrator to update the number of mds instances
        orch = Orchestrator()
        orch.apply_mds(name)

    def volume_ls(self) -> CephFSVolumeListModel:

        cmd = {
            "prefix": "fs volume ls",
            "format": "json"
        }
        try:
            res = self.mgr.call(cmd)
        except CephCommandError as e:
            raise CephFSError(e) from e
        return CephFSVolumeListModel(
            volumes=parse_obj_as(List[CephFSNameModel], res)
        )

    def ls(self) -> List[CephFSListEntryModel]:
        cmd = {
            "prefix": "fs ls",
            "format": "json"
        }
        try:
            res = self.mon.call(cmd)
        except CephCommandError as e:
            raise CephFSError(e) from e
        return parse_obj_as(List[CephFSListEntryModel], res)

    def get_fs_info(self, name: str) -> CephFSListEntryModel:
        ls: List[CephFSListEntryModel] = self.ls()
        for fs in ls:
            if fs.name == name:
                return fs
        raise CephFSError(f"unknown filesystem {name}")
