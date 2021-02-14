# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from enum import Enum
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel
from gravel.controllers.orch.ceph import Mon
from gravel.controllers.orch.cephfs import CephFS, CephFSError
from gravel.controllers.orch.models import CephFSListEntryModel, CephOSDPoolEntryModel
from gravel.controllers.resources import storage
from gravel import gstate


class ServiceError(Exception):
    pass


class UnknownServiceError(ServiceError):
    pass


class ServiceExistsError(ServiceError):
    pass


class NotEnoughSpaceError(ServiceError):
    pass


class ServiceTypeEnum(str, Enum):
    CEPHFS = "cephfs"
    NFS = "nfs"
    RBD = "rbd"
    ISCSI = "iscsi"
    RGW = "rgw"


class ServiceModel(BaseModel):
    name: str
    reservation: int
    type: ServiceTypeEnum
    pools: List[int]
    replicas: int


class StateModel(BaseModel):
    state: Dict[str, ServiceModel]


class Services:

    _services: Dict[str, ServiceModel]

    def __init__(self):
        self._services = {}
        self._load()

    def create(self, name: str,
               type: ServiceTypeEnum,
               size: int,
               replicas: int
               ) -> ServiceModel:
        if type != ServiceTypeEnum.CEPHFS:
            raise NotImplementedError("only cephfs is currently supported")
        if name in self._services:
            raise ServiceExistsError(f"service {name} already exists")

        estimated_size: int = size * replicas
        cur_reservations: int = self.total_reservation
        if (cur_reservations + estimated_size) > storage.available:
            raise NotEnoughSpaceError(
                f"needed: {estimated_size}, "\
                f"reserved: {cur_reservations}, "\
                f"available: {storage.available}"
        )

        svc: ServiceModel = ServiceModel(
            name=name,
            reservation=size,
            type=type,
            pools=[],
            replicas=replicas
        )
        self._create_service(svc)
        self._services[name] = svc
        self._save()
        return svc

    def remove(self, name: str):
        pass

    def ls(self) -> List[ServiceModel]:
        return [x for x in self._services.values()]

    @property
    def total_reservation(self) -> int:
        total: int = 0
        for service in self._services.values():
            total += service.reservation
        return total

    def __contains__(self, name: str) -> bool:
        return name in self._services

    def get(self, name: str) -> ServiceModel:
        if name not in self._services:
            raise UnknownServiceError(name)
        return self._services[name]

    def _create_service(self, svc: ServiceModel) -> None:
        if svc.type == ServiceTypeEnum.CEPHFS:
            self._create_cephfs(svc)
        else:
            raise NotImplementedError("only cephfs is currently supported")

    def _create_cephfs(self, svc: ServiceModel) -> None:
        cephfs = CephFS()
        try:
            cephfs.create(svc.name)
        except CephFSError as e:
            raise ServiceError("unable to create cephfs service") from e

        try:
            fs: CephFSListEntryModel = cephfs.get_fs_info(svc.name)
        except CephFSError as e:
            raise ServiceError("unable to list cephfs filesystems") from e
        assert fs.name == svc.name

        mon = Mon()
        pools: List[CephOSDPoolEntryModel] = mon.get_pools()

        def get_pool(name: str) -> CephOSDPoolEntryModel:
            for pool in pools:
                if pool.pool_name == name:
                    return pool
            raise ServiceError(f"unknown pool {name}")

        metadata_pool = get_pool(fs.metadata_pool)
        if metadata_pool.size != svc.replicas:
            mon.set_pool_size(metadata_pool.pool_name, svc.replicas)
        svc.pools.append(metadata_pool.pool)

        for name in fs.data_pools:
            data_pool = get_pool(name)
            if data_pool.size != svc.replicas:
                mon.set_pool_size(data_pool.pool_name, svc.replicas)
            svc.pools.append(data_pool.pool)

    def _save(self) -> None:
        assert gstate.config.options.service_state_path
        path = Path(gstate.config.options.service_state_path)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        state = StateModel(state=self._services)
        path.write_text(state.json(indent=2))

    def _load(self) -> None:
        assert gstate.config.options.service_state_path
        path = Path(gstate.config.options.service_state_path)
        if not path.exists():
            return
        state: StateModel = StateModel.parse_file(path)
        self._services = state.state
