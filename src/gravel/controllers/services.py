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
from typing import Dict, List, Tuple
from logging import Logger
from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel
from pydantic.fields import Field

from gravel.controllers.orch.ceph import Mon
from gravel.controllers.orch.cephfs import CephFS, CephFSError
from gravel.controllers.orch.models import (
    CephFSListEntryModel,
    CephOSDPoolEntryModel
)
from gravel.controllers.gstate import gstate
from gravel.controllers.resources.devices import (
    DeviceHostModel,
    Devices,
    get_devices
)
from gravel.controllers.resources.storage import (
    Storage, StoragePoolModel,
    get_storage
)


logger: Logger = fastapi_logger


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
    # NFS = "nfs"
    # RBD = "rbd"
    # ISCSI = "iscsi"
    # RGW = "rgw"


class ServiceModel(BaseModel):
    name: str
    reservation: int
    type: ServiceTypeEnum
    pools: List[int]
    replicas: int
    raw_size: int


class StateModel(BaseModel):
    state: Dict[str, ServiceModel]


class ServiceRequirementsModel(BaseModel):
    reserved: int = Field(0, title="Total existing reservations (bytes)")
    available: int = Field(0, title="Available storage space (bytes)")
    required: int = Field(0, title="Required additional storage space (bytes)")


class RedundancyConstraints(BaseModel):
    max_replicas: int = Field(0, title="maximum provided replicas")


class AvailabilityConstraints(BaseModel):
    hosts: int = Field(0, title="number of available hosts")


class AllocationConstraints(BaseModel):
    allocated: int = Field(0, title="Allocated space (byte)")
    available: int = Field(0, title="Available space (byte)")


class ConstraintsModel(BaseModel):
    allocations: AllocationConstraints = \
        Field(AllocationConstraints(), title="allocations constraints")
    redundancy: RedundancyConstraints = \
        Field(RedundancyConstraints(), title="redundancy constraints")
    availability: AvailabilityConstraints = \
        Field(AvailabilityConstraints(), title="availability constraints")


class ServiceStorageModel(BaseModel):
    name: str = Field(0, title="Service name")
    used: int = Field(0, title="Used space (byte)")
    avail: int = Field(0, title="Available space (byte)")
    allocated: int = Field(0, title="Allocated space (bytes)")
    utilization: float = Field(0, title="Utilization")


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
        if name in self._services:
            raise ServiceExistsError(f"service {name} already exists")

        feasible, requirements = self.check_requirements(size, replicas)
        if not feasible:
            raise NotEnoughSpaceError(requirements.json())

        svc: ServiceModel = ServiceModel(
            name=name,
            reservation=size,
            type=type,
            pools=[],
            replicas=replicas,
            raw_size=size*replicas
        )

        if svc.type == ServiceTypeEnum.CEPHFS:
            self._create_cephfs(svc)
        else:
            raise NotImplementedError(f"unknown service type: {svc.type}")

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

    @property
    def total_raw_reservation(self) -> int:
        total: int = 0
        for service in self._services.values():
            total += (service.reservation * service.replicas)
        return total

    @property
    def available_space(self) -> int:
        storage: Storage = get_storage()
        total_storage: int = storage.total
        return (total_storage - self.total_raw_reservation)

    def __contains__(self, name: str) -> bool:
        return name in self._services

    def get(self, name: str) -> ServiceModel:
        if name not in self._services:
            raise UnknownServiceError(name)
        return self._services[name]

    @property
    def constraints(self) -> ConstraintsModel:
        """
        Calculate constraints for service deployment. These are generic and not
        tied to any particular service's requirements.
        """
        devices_ctrl: Devices = get_devices()
        devs_per_host: Dict[str, DeviceHostModel] = \
            devices_ctrl.devices_per_host

        logger.debug(f"get constraints, hosts = {devs_per_host}")

        hosts: List[str] = \
            [h for h, d in devs_per_host.items() if len(d.devices) > 0]
        num_hosts: int = len(hosts)

        availability: AvailabilityConstraints = \
            AvailabilityConstraints(hosts=num_hosts)

        max_devs: int = 0
        min_devs: int = -1
        for h in hosts:
            ndevs: int = len(devs_per_host[h].devices)
            max_devs = max(max_devs, ndevs)
            min_devs = ndevs if min_devs < 0 else min(min_devs, ndevs)

        if num_hosts == 1:
            assert max_devs == min_devs

        elif min_devs < max_devs:
            # TODO: warn about unbalanced cluster
            pass

        # if we have one host, our redundancy is tied to said host's devices,
        # and thus we max out at the total number of devices; if we have
        # multiple hosts, we want to replicate across hosts, and thus we're tied
        # to the number of hosts.
        #
        redundancy: RedundancyConstraints = RedundancyConstraints()
        redundancy.max_replicas = max_devs if num_hosts == 1 else num_hosts

        allocations: AllocationConstraints = AllocationConstraints(
            allocated=self.total_raw_reservation,
            available=self.available_space
        )

        return ConstraintsModel(
            allocations=allocations,
            redundancy=redundancy,
            availability=availability
        )

    def check_requirements(
        self, size: int, replicas: int
    ) -> Tuple[bool, ServiceRequirementsModel]:
        required: int = size*replicas
        reserved: int = self.total_raw_reservation
        available: int = self.available_space
        feasible: bool = (required <= available)
        requirements = ServiceRequirementsModel(
            reserved=reserved,
            available=available,
            required=required
        )
        return feasible, requirements

    def get_stats(self) -> Dict[str, ServiceStorageModel]:
        """
        Obtain services statistics, including how much space is currently being
        used for each service, and utilization as a function of the used space
        and the allocated space.
        """
        storage: Storage = get_storage()
        storage_pools: Dict[int, StoragePoolModel] = storage.usage().pools_by_id

        services: Dict[str, ServiceStorageModel] = {}

        for svc in self._services.values():
            allocated: int = svc.reservation
            used_bytes: int = 0

            for poolid in svc.pools:
                if poolid not in storage_pools:
                    # given storage pools are updated periodically, we may not
                    # have up-to-date statistics yet; and that means we might be
                    # missing a pool. Jump over said pool if so.
                    continue
                stats = storage_pools[poolid].stats
                used_bytes += stats.used

            available: int = allocated - used_bytes
            utilization: float = used_bytes / allocated

            services[svc.name] = ServiceStorageModel(
                name=svc.name,
                used=used_bytes,
                avail=available,
                allocated=allocated,
                utilization=utilization
            )

        return services

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

        # create cephfs default user
        logger.debug("authorize default user")
        try:
            cephfs.authorize(svc.name, "default")
            logger.info(f"created cephfs client for service '{svc.name}'")
        except CephFSError as e:
            logger.error(f"Unable to authorize cephfs client: {str(e)}")
            logger.exception(e)
            # do nothing else, the service still works without an authorized
            # client.

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
