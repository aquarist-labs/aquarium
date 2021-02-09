# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.


from typing import List

from pydantic.tools import parse_obj_as
from gravel.controllers.orch.ceph import CephCommandError, Mgr, Mon

from gravel.controllers.orch.models \
    import CephFSNameModel, CephFSVolumeListModel


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
            res = self.mgr.call(cmd)
        except CephCommandError as e:
            raise CephFSError(e) from e
        # this command does not support json at this time, and will output
        # free-form text instead. We are not going to parse it, but we'll make
        # sure we've got something out of it.
        assert "result" in res
        assert len(res["result"]) > 0

    def ls(self) -> CephFSVolumeListModel:

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
