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

import errno
from typing import List, Optional

from pydantic.tools import parse_obj_as
from gravel.controllers.orch.ceph import CephCommandError, Mgr, Mon

from gravel.controllers.orch.models import (
    CephFSAuthorizationModel,
    CephFSListEntryModel,
    CephFSNameModel,
    CephFSVolumeListModel,
)
from gravel.controllers.orch.orchestrator import Orchestrator


class CephFSError(Exception):
    pass


class CephFSNoAuthorizationError(CephFSError):
    pass


class CephFS:

    mgr: Mgr
    mon: Mon

    def __init__(self, mgr: Mgr, mon: Mon):
        self.mgr = mgr
        self.mon = mon

    def create(self, name: str) -> None:

        cmd = {"prefix": "fs volume create", "name": name}
        try:
            # this is expected to be a silent command
            self.mgr.call(cmd)
        except CephCommandError as e:
            raise CephFSError(e) from e

        # schedule orchestrator to update the number of mds instances
        orch = Orchestrator(self.mgr)
        orch.apply_mds(name)

    def volume_ls(self) -> CephFSVolumeListModel:

        cmd = {"prefix": "fs volume ls", "format": "json"}
        try:
            res = self.mgr.call(cmd)
        except CephCommandError as e:
            raise CephFSError(e) from e
        return CephFSVolumeListModel(
            volumes=parse_obj_as(List[CephFSNameModel], res)
        )

    def ls(self) -> List[CephFSListEntryModel]:
        cmd = {"prefix": "fs ls", "format": "json"}
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

    def authorize(self, fsname: str, clientid: str) -> CephFSAuthorizationModel:
        assert fsname and clientid
        cmd = {
            "prefix": "fs authorize",
            "filesystem": fsname,
            "entity": f"client.{fsname}-{clientid}",
            "caps": ["/", "rw"],
            "format": "json",
        }
        try:
            res = self.mon.call(cmd)
        except CephCommandError as e:
            raise CephFSError(str(e)) from e
        lst = parse_obj_as(List[CephFSAuthorizationModel], res)
        assert len(lst) == 1
        return lst[0]

    def get_authorization(
        self, fsname: str, clientid: Optional[str]
    ) -> CephFSAuthorizationModel:

        if not clientid:
            clientid = "default"

        cmd = {
            "prefix": "auth get",
            "entity": f"client.{fsname}-{clientid}",
            "format": "json",
        }
        try:
            res = self.mon.call(cmd)
        except CephCommandError as e:
            if e.rc == errno.ENOENT:
                raise CephFSNoAuthorizationError(e.message)
            raise CephFSError(str(e)) from e
        lst = parse_obj_as(List[CephFSAuthorizationModel], res)
        if len(lst) == 0:
            raise CephFSNoAuthorizationError()
        return lst[0]
