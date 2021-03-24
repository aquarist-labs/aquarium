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

from typing import Any, Dict, Optional

from gravel.controllers.orch.ceph import CephCommandError, Mgr


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
            'type': 'cephfs',  # TODO: fix upstream
            'clusterid': name,
        }
        if placement:
            cmd['placement'] = placement
        return self._call(cmd)['result']
