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

import shlex
from logging import Logger
from pathlib import Path
from typing import Dict, List, Optional

from fastapi.logger import logger as fastapi_logger
from pydantic.main import BaseModel

from gravel.controllers.errors import GravelError
from gravel.controllers.inventory.disks import DiskDevice, get_storage_devices
from gravel.controllers.utils import aqr_run_cmd

logger: Logger = fastapi_logger


class UnknownDeviceError(GravelError):
    pass


class UnavailableDeviceError(GravelError):
    pass


class MountError(GravelError):
    pass


class LVMError(GravelError):
    pass


class SystemDiskNotMountedError(GravelError):
    pass


class OverlayError(GravelError):
    pass


class MountEntry(BaseModel):
    source: str
    dest: str
    overlay: bool


AQR_SYSTEM_PATH = "/var/lib/aquarium-system"


def get_mounts() -> List[MountEntry]:
    """Obtain mounts from the system."""

    def _get_overlay_src(opts: str) -> str:
        optlst: List[str] = opts.split(",")
        upper: Optional[str] = None
        for e in optlst:
            if e.startswith("upperdir"):
                path = Path(e.split("=")[1])
                upper = path.parent.as_posix()
        if upper is None or len(upper) == 0:
            raise OverlayError(
                f"Unable to find upper dir from options: {opts}."
            )
        return upper

    proc: Path = Path("/proc/mounts")
    assert proc.exists()

    lst: List[MountEntry] = []
    with proc.open(mode="r", encoding="utf-8") as f:
        for line in f.readlines():
            fields: List[str] = line.split(" ")
            if len(fields) < 4:
                continue

            fields = [x.strip() for x in fields]
            src, dst, fstype, opts = fields[0:4]
            is_overlay = fstype == "overlay"
            if is_overlay:
                try:
                    src = _get_overlay_src(opts)
                except OverlayError as e:
                    raise OverlayError(
                        f"Unable to find overlay source for {dst}: {e.message}"
                    )

            lst.append(MountEntry(source=src, dest=dst, overlay=is_overlay))
    return lst


async def lvm(args: List[str]) -> str:
    cmd: List[str] = ["lvm"] + args
    retcode, out, err = await aqr_run_cmd(cmd)

    if retcode != 0:
        raise LVMError(msg=err)
    return out if out is not None else ""


class SystemDisk:

    _overlaydirs: Dict[str, str] = {
        "etc": "/etc",
        "logs": "/var/log",
        "aquarium": "/var/lib/aquarium",
        "roothome": "/root",
        "sysctl": "/usr/lib/sysctl.d",
    }
    _bindmounts: Dict[str, str] = {"ceph": "/var/lib/ceph"}

    def __init__(self) -> None:
        pass

    @property
    def mounted(self):
        mounts: List[MountEntry] = get_mounts()
        for entry in mounts:
            if (
                entry.source == "/dev/mapper/aquarium-systemdisk"
                and entry.dest == AQR_SYSTEM_PATH
            ):
                return True
        return False

    async def exists(self) -> bool:
        """Checks whether a System Disk exists in the system."""

        lvmcmd = shlex.split("lvs --noheadings -o vg_name,lv_name @aquarium")
        try:
            out = await lvm(lvmcmd)
        except LVMError:
            return False

        lst = [x.strip() for x in out.split("\n") if len(x) > 0]
        if len(lst) == 0:
            return False

        lvs = [lv.split()[1] for lv in lst]
        if "containers" not in lvs:
            # systemdisk does not have a containers LV, we're in error state.
            raise LVMError(msg="System Disk missing Containers LV.")
        elif "systemdisk" not in lvs:
            # systemdisk does not have a persistent state LV, we're in error
            # state.
            raise LVMError(msg="System Disk missing persistent state LV.")

        return True

    async def create(self, devicestr: str) -> None:

        logger.debug(f"prepare system disk: {devicestr}")
        devs: List[DiskDevice] = await get_storage_devices()
        device: Optional[DiskDevice] = next(
            (d for d in devs if d.path == devicestr), None
        )

        # ascertain whether we can use this device
        if not device:
            raise UnknownDeviceError(f"Device {devicestr} not known.")
        elif not device.available:
            raise UnavailableDeviceError(
                f"Device {devicestr} is not available."
            )

        # create partitions
        logger.debug(f"prepare system disk: device: {device}")
        devpath = device.path

        def _create_overlay_dir(path: Path, dirname: str) -> None:
            assert path.exists()
            dirpath: Path = path.joinpath(dirname)
            assert not dirpath.exists()
            dirpath.mkdir()
            dirpath.joinpath("overlay").mkdir()
            dirpath.joinpath("temp").mkdir()

        try:
            # create lvm volume
            await lvm(shlex.split(f"pvcreate {devpath}"))
            await lvm(
                shlex.split(f"vgcreate aquarium {devpath} --addtag @aquarium")
            )
            await lvm(shlex.split("lvcreate -l 50%VG -n systemdisk aquarium"))
            await lvm(shlex.split("lvcreate -l 50%VG -n containers aquarium"))

            lvmdev: Path = Path("/dev/mapper/aquarium-systemdisk")
            assert lvmdev.exists()
            ctrdev: Path = Path("/dev/mapper/aquarium-containers")
            assert ctrdev.exists()

            # format systemdisk with xfs
            await aqr_run_cmd(shlex.split(f"mkfs.xfs -m bigtime=1 {lvmdev}"))
            # format containers lv with btrfs
            await aqr_run_cmd(shlex.split(f"mkfs.btrfs {ctrdev}"))

            aqrmntpath: Path = Path(AQR_SYSTEM_PATH)
            aqrmntpath.mkdir(exist_ok=True, parents=True)

            await self.mount()

            for d in self._overlaydirs.keys():
                _create_overlay_dir(aqrmntpath, d)

            # some directories (like ceph's) can't be overlayed due to weirdness
            # ensued, so we'll bind mount them later.
            for d in self._bindmounts.keys():
                ourpath: Path = aqrmntpath.joinpath(d)
                assert not ourpath.exists()
                ourpath.mkdir()

            await self.unmount()

        except Exception as e:
            logger.error(f"prepare system disk > {str(e)}")
            logger.exception(e)
            raise e

    async def mount(self) -> None:
        await self._mount("systemdisk", Path(AQR_SYSTEM_PATH))
        await self._mount("containers", Path("/var/lib/containers"))

    async def _mount(self, src: str, dest: Path) -> None:
        devpath = Path(f"/dev/mapper/aquarium-{src}")
        assert devpath.exists()
        dest.mkdir(exist_ok=True, parents=True)

        aqrdev: str = devpath.as_posix()
        aqrmnt: str = dest.as_posix()

        try:
            await aqr_run_cmd(shlex.split(f"mount {aqrdev} {aqrmnt}"))
        except Exception as e:
            raise MountError(msg=str(e))

    async def unmount(self) -> None:
        await self._unmount(Path(AQR_SYSTEM_PATH))
        await self._unmount(Path("/var/lib/containers"))

    async def _unmount(self, mnt: Path) -> None:
        if not mnt.exists():
            raise MountError(msg=f"The {mnt} mount point does not exist.")

        try:
            await aqr_run_cmd(shlex.split(f"umount {mnt}"))
        except Exception as e:
            raise MountError(msg=str(e))

    async def enable(self) -> None:
        if not self.mounted:
            try:
                await self.mount()
            except MountError as e:
                raise OverlayError(msg=e.message)

        async def _overlay(lower: str, upper: str, work: str):
            mntcmd = (
                "mount -t overlay "
                f"-o lowerdir={lower},upperdir={upper},workdir={work} "
                f"overlay {lower}"
            )
            await aqr_run_cmd(shlex.split(mntcmd))

        mounts: List[MountEntry] = get_mounts()

        def _is_mounted(src: str, dest: str, overlay: bool) -> bool:
            for entry in mounts:
                if overlay and entry.dest == dest and entry.source == src:
                    return True
                elif not overlay and entry.dest == dest:
                    return True
            return False

        for upper, lower in self._overlaydirs.items():
            aqrpath: Path = Path(AQR_SYSTEM_PATH)
            upperpath: Path = aqrpath.joinpath(upper)
            overlaypath: Path = upperpath.joinpath("overlay")
            temppath: Path = upperpath.joinpath("temp")
            lowerpath: Path = Path(lower)
            assert overlaypath.exists() and overlaypath.is_dir()
            assert temppath.exists() and temppath.is_dir()

            if _is_mounted(upperpath.as_posix(), lower, True):
                logger.info(f"{lower} is already overlayed in {upper}.")
                continue

            lowerpath.mkdir(parents=True, exist_ok=True)
            assert lowerpath.exists() and lowerpath.is_dir()

            try:
                await _overlay(
                    lower, overlaypath.as_posix(), temppath.as_posix()
                )
            except Exception as e:
                raise OverlayError(
                    f"Unable to overlay {upper} on {lower}: {str(e)}"
                )

        for ours, theirs in self._bindmounts.items():
            ourpath: Path = Path(AQR_SYSTEM_PATH).joinpath(ours)
            theirpath: Path = Path(theirs)
            assert ourpath.exists()

            if _is_mounted(ourpath.as_posix(), theirs, False):
                logger.info(f"{ourpath} already mounted at {theirs}.")
                continue

            theirpath.mkdir(parents=True, exist_ok=True)

            try:
                await aqr_run_cmd(
                    [
                        "mount",
                        "--bind",
                        ourpath.as_posix(),
                        theirpath.as_posix(),
                    ]
                )
            except Exception as e:
                raise MountError(
                    f"Unable to bind mount {ourpath} to {theirpath}: {str(e)}"
                )
