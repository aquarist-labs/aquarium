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

from enum import Enum
from pathlib import Path
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


class NFSBackingStoreEnum(str, Enum):
    CEPHFS = "cephfs"
    RGW = "rgw"


class NFSExportModel(BaseModel):
    export_id: int
    path: str
    pseudo: str
    access_type: str
    squash: str
    security_label: bool
    protocols: List[str]
    transports: List[str]
    fsal: Dict  # TODO: create model for this?
    clients: List[str]


class NFSError(Exception):
    pass


class NFS:
    mgr: Mgr

    def __init__(self, ceph_mgr: Mgr):
        self.mgr = ceph_mgr

    def _call(self, cmd: Dict[str, Any]) -> Any:
        try:
            return self.mgr.call(cmd)
        except CephCommandError as e:
            raise NFSError(e) from e


class NFSService(NFS):
    def create(self, service_id: str, placement: Optional[str]) -> str:
        cmd = {
            "prefix": "nfs cluster create",
            "type": "cephfs",  # TODO: pending https://github.com/ceph/ceph/pull/40411
            "clusterid": service_id,
        }
        if placement:
            cmd["placement"] = placement
        return self._call(cmd)["result"]

    def update(self, service_id: str, placement: str) -> str:
        res = self._call(
            {
                "prefix": "nfs cluster update",
                "clusterid": service_id,
                "placement": placement,
            }
        )
        return res["result"]

    def delete(self, service_id: str) -> str:
        res = self._call(
            {
                "prefix": "nfs cluster delete",
                "clusterid": service_id,
            }
        )
        return res["result"]

    def ls(self) -> List[str]:
        res = self._call(
            {
                "prefix": "nfs cluster ls",
                "format": "json",
            }
        )
        return res["result"].split() if res.get("result") else []

    def info(self, service_id: Optional[str] = None) -> List[NFSServiceModel]:
        cmd = {
            "prefix": "nfs cluster info",
            "format": "json",
        }
        if service_id:
            cmd["clusterid"] = service_id

        res = self._call(cmd)

        ret: List[NFSServiceModel] = []
        for service_id in res:
            daemons = parse_obj_as(List[NFSDaemonModel], res[service_id])
            ret.append(NFSServiceModel(service_id=service_id, daemons=daemons))
        return ret


class NFSExport(NFS):
    def create(
        self,
        service_id: str,
        binding: str,
        fs_type: NFSBackingStoreEnum,
        fs_name: str,
        fs_path: Optional[str] = None,
        readonly: bool = False,
    ) -> NFSExportModel:
        binding = str(Path("/").joinpath(binding))
        cmd = {
            # TODO: fix upstream: prefix contains `fs_type`
            # TODO: fix upstream: `rgw` is not currently supported
            "prefix": f"nfs export create {fs_type}",
            "fsname": fs_name,
            "clusterid": service_id,
            "binding": binding,
            "readonly": readonly,
        }
        if fs_path:
            cmd["path"] = fs_path

        # TODO: fix upstream: add json formatter?
        #       output is sometimes json, sometimes str
        res = self._call(cmd)
        if "result" in res:
            # TODO: fix upstream: return proper errno
            raise NFSError(res["result"])

        # find the newly created export
        # TODO: fix upstream: return `export_id` in the create response?
        for export in self.info(service_id):
            # TODO: fix upstream: `binding`, `bind`, `path`, `pseudo` ??
            if export.pseudo == binding:
                return export

        # cannot find the export, did an error occur?
        if "result" in res:
            raise NFSError(res["result"])
        raise NFSError(f"failed to create nfs export: {res}")

    def delete(self, service_id: str, export_id: int):
        for export in self.info(service_id):
            if export.export_id == export_id:
                res = self._call(
                    {
                        "prefix": "nfs export delete",
                        "clusterid": service_id,
                        # TODO: fix upstream: delete by `export_id`?
                        "binding": str(Path("/").joinpath(export.pseudo)),
                    }
                )
                return res["result"]
        # TODO: return errno to create HTTP 404
        raise NFSError("export not found")

    def ls(self, service_id: str) -> List[int]:
        return sorted([e.export_id for e in self.info(service_id)])

    def info(self, service_id: str) -> List[NFSExportModel]:
        cmd = {
            "prefix": "nfs export ls",
            "clusterid": service_id,
            "detailed": True,  # TODO: fix upstream: `detailed` -> `detail`?
            "format": "json",
        }

        res = self._call(cmd)

        ret: List[NFSExportModel] = []
        for export in res:
            ret.append(NFSExportModel(**export))
        return ret
