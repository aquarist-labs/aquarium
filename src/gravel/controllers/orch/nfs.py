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

from typing import Any, Dict, List, Optional

from pydantic.tools import parse_obj_as
from pydantic import BaseModel

from gravel.controllers.orch.ceph import CephCommandError, Mgr


class NFSDaemonModel(BaseModel):
    hostname: str
    ip: List[str]
    port: int


class NFSServiceModel(BaseModel):
    name: str
    daemons: List[NFSDaemonModel]


class NFSError(Exception):
    pass


class NFSService:
    mgr: Mgr

    def __init__(self):
        self.mgr = Mgr()

    def _call(self, cmd: Dict[str, Any]) -> Any:
        try:
            return self.mgr.call(cmd)
        except CephCommandError as e:
            raise NFSError(e) from e

    def create(self, name: str, placement: Optional[str]) -> str:
        cmd = {
            'prefix': 'nfs cluster create',
            'type': 'cephfs',  # TODO: pending https://github.com/ceph/ceph/pull/40411
            'clusterid': name,
        }
        if placement:
            cmd['placement'] = placement
        return self._call(cmd)['result']

    def update(self, name: str, placement: str) -> str:
        res = self._call({
            'prefix': 'nfs cluster update',
            'clusterid': name,
            'placement': placement,
        })
        return res['result']

    def delete(self, name: str) -> str:
        res = self._call({
            'prefix': 'nfs cluster delete',
            'clusterid': name,
        })
        return res['result']

    def ls(self) -> List[str]:
        res = self._call({
            'prefix': 'nfs cluster ls',
            'format': 'json',
        })
        return res['result'].split() if res.get('result') else []

    def info(self, name: Optional[str] = None) -> List[NFSServiceModel]:
        cmd = {
            'prefix': 'nfs cluster info',
            'format': 'json',
        }
        if name:
            cmd['clusterid'] = name

        res = self._call(cmd)

        ret: List[NFSServiceModel] = []
        for name in res:
            daemons = parse_obj_as(List[NFSDaemonModel], res[name])
            ret.append(
                NFSServiceModel(
                    name=name,
                    daemons=daemons
                )
            )
        return ret
