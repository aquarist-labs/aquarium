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

import asyncio
from enum import Enum
from pathlib import Path
from typing import Any, Coroutine, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, validator

from gravel.controllers.utils import HWEntryModel, lshw

# hard coded for now, this should be configurable and a saner value.
MIN_DISK_SIZE = 10 * 1024 * 1024 * 1024  # 10 GB


class RejectionReasonEnum(int, Enum):
    IN_USE = 1
    TOO_SMALL = 2
    REMOVABLE_DEVICE = 3


def _make_unknown(value: Optional[str]) -> str:
    if value is None:
        return "Unknown"
    return value


class DiskDevice(BaseModel):
    id: str
    name: str
    path: str
    product: str
    vendor: str
    size: int
    rotational: bool
    available: bool
    rejected_reasons: List[RejectionReasonEnum] = Field([])

    _validate_product = validator("product", pre=True, allow_reuse=True)(
        _make_unknown
    )

    _validate_vendor = validator("vendor", pre=True, allow_reuse=True)(
        _make_unknown
    )


async def get_hw_storage_devices() -> Union[List[HWEntryModel], None]:
    async def _get_devices(
        entry: HWEntryModel,
    ) -> Union[List[HWEntryModel], None]:
        if not entry.children or len(entry.children) == 0:
            return None

        if entry.cls == "storage":
            return [entry]

        coros: List[Coroutine[Any, Any, Union[List[HWEntryModel], None]]] = []
        for child in entry.children:
            coros.append(_get_devices(child))

        ret = await asyncio.gather(*coros)
        storage: List[HWEntryModel] = []
        if not ret:
            return None

        for e in ret:
            if e is None:
                continue
            storage.extend(e)

        return storage

    system = await lshw()
    return await _get_devices(system)


async def _get_sys_rotational(blkname: str) -> bool:
    path = Path(f"/sys/block/{blkname}/queue/rotational")
    if not path.exists():
        raise Exception()
    return bool(int(path.read_text("utf-8")))


def _get_availability(
    disk: HWEntryModel,
) -> Tuple[bool, List[RejectionReasonEnum]]:
    reasons: List[RejectionReasonEnum] = []

    if (disk.children is not None and len(disk.children) >= 0) or (
        disk.capabilities is not None
        and "lvm2" in disk.capabilities
        and disk.capabilities["lvm2"] is True
    ):
        reasons.append(RejectionReasonEnum.IN_USE)

    assert disk.size is not None
    if disk.size < MIN_DISK_SIZE:
        reasons.append(RejectionReasonEnum.TOO_SMALL)

    if disk.capabilities is not None and "removable" in disk.capabilities:
        reasons.append(RejectionReasonEnum.REMOVABLE_DEVICE)

    available = len(reasons) == 0
    return available, reasons


async def _get_disk_device(disk: HWEntryModel) -> DiskDevice:
    assert disk.cls == "disk" or disk.cls == "volume"
    assert disk.logicalname is not None
    assert isinstance(disk.logicalname, str)
    assert disk.logicalname.startswith("/dev/")

    blkname = disk.logicalname.replace("/dev/", "")
    available, rejection_reasons = _get_availability(disk)
    rotational = await _get_sys_rotational(blkname)

    assert disk.units is None or disk.units == "bytes"

    return DiskDevice(
        id=disk.id,
        name=blkname,
        path=disk.logicalname,
        product=disk.product,
        vendor=disk.vendor,
        size=disk.size,
        rotational=rotational,
        available=available,
        rejected_reasons=rejection_reasons,
    )


async def _get_storage_devices(hwdev: HWEntryModel) -> List[DiskDevice]:
    assert hwdev.cls == "storage"
    assert hwdev.children is not None and len(hwdev.children) > 0

    coros = [
        _get_disk_device(disk) for disk in hwdev.children if disk.id != "cdrom"
    ]
    return list(await asyncio.gather(*coros))


async def get_storage_devices() -> List[DiskDevice]:
    storage: Union[List[HWEntryModel], None] = await get_hw_storage_devices()
    if not storage:
        return []

    coros = [_get_storage_devices(entry) for entry in storage]
    res = await asyncio.gather(*coros)

    devs: List[DiskDevice] = []
    for dev in res:
        devs.extend(dev)
    return devs
