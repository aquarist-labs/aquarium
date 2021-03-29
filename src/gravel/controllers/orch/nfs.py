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
    service_id: str
    daemons: List[NFSDaemonModel]


class NFSError(Exception):
    pass


class NFS:
    mgr: Mgr

    def __init__(self):
        self.mgr = Mgr()

    def _call(self, cmd: Dict[str, Any]) -> Any:
        try:
            return self.mgr.call(cmd)
        except CephCommandError as e:
            raise NFSError(e) from e


class NFSService(NFS):
    def create(self, service_id: str, placement: Optional[str]) -> str:
        cmd = {
            'prefix': 'nfs cluster create',
            'type': 'cephfs',  # TODO: pending https://github.com/ceph/ceph/pull/40411
            'clusterid': service_id,
        }
        if placement:
            cmd['placement'] = placement
        return self._call(cmd)['result']

    def update(self, service_id: str, placement: str) -> str:
        res = self._call({
            'prefix': 'nfs cluster update',
            'clusterid': service_id,
            'placement': placement,
        })
        return res['result']

    def delete(self, service_id: str) -> str:
        res = self._call({
            'prefix': 'nfs cluster delete',
            'clusterid': service_id,
        })
        return res['result']

    def ls(self) -> List[str]:
        res = self._call({
            'prefix': 'nfs cluster ls',
            'format': 'json',
        })
        return res['result'].split() if res.get('result') else []

    def info(self, service_id: Optional[str] = None) -> List[NFSServiceModel]:
        cmd = {
            'prefix': 'nfs cluster info',
            'format': 'json',
        }
        if service_id:
            cmd['clusterid'] = service_id

        res = self._call(cmd)

        ret: List[NFSServiceModel] = []
        for service_id in res:
            daemons = parse_obj_as(List[NFSDaemonModel], res[service_id])
            ret.append(
                NFSServiceModel(
                    service_id=service_id,
                    daemons=daemons
                )
            )
        return ret
