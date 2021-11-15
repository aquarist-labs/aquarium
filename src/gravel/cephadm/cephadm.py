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
import json
import os
import tempfile
import time
from io import StringIO
from logging import Logger
from typing import IO, Callable, List, Optional, Tuple

import pydantic
from fastapi.logger import logger as fastapi_logger
from pydantic.tools import parse_obj_as

from gravel.controllers.config import ContainersOptionsModel

from .models import HostFactsModel, VolumeDeviceModel

logger: Logger = fastapi_logger


class CephadmError(Exception):
    pass


class Cephadm:

    _config: ContainersOptionsModel
    cephadm: List[str]

    def __init__(self) -> None:
        self._config = ContainersOptionsModel()
        if os.path.exists("./gravel/cephadm/cephadm.bin"):
            # dev environment
            self.cephadm = ["sudo", "./gravel/cephadm/cephadm.bin"]
        else:
            # deployment environment
            self.cephadm = ["sudo", "cephadm"]

    def set_config(self, config: ContainersOptionsModel) -> None:
        self._config = config

    async def call(
        self,
        cmd: List[str],
        noimage: bool = False,
        outcb: Optional[Callable[[str], None]] = None,
    ) -> Tuple[str, str, int]:

        assert len(cmd) > 0
        cmdlst: List[str] = list(self.cephadm)
        if not noimage:
            image = self._config.get_image()
            cmdlst.extend(["--image", image])
        cmdlst.extend(cmd)
        logger.debug(f"call with {self.cephadm}")
        logger.debug(f"call: {cmdlst}")

        process = await asyncio.create_subprocess_exec(
            *cmdlst,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        assert process.stdout
        assert process.stderr

        stdout, stderr = await asyncio.gather(
            self._tee(process.stdout, outcb), self._tee(process.stderr, outcb)
        )
        retcode = await asyncio.wait_for(process.wait(), None)

        return stdout, stderr, retcode

    async def run_in_background(self, cmd: List[str]) -> None:
        pass

    async def _tee(
        self,
        reader: asyncio.StreamReader,
        cb: Optional[Callable[[str], None]] = None,
    ) -> str:
        collected = StringIO()
        async for line in reader:
            msg = line.decode("utf-8")
            collected.write(msg)
            if cb:
                cb(msg)
        return collected.getvalue()

    #
    # command wrappers
    #

    async def bootstrap(
        self, addr: str, percentcb: Optional[Callable[[int], None]] = None
    ) -> Tuple[str, str, int]:

        if not addr:
            raise CephadmError("address not specified")

        msg_to_percent: List[Tuple[str, int]] = [
            ("cluster fsid", 5),
            ("pulling container image", 7),
            ("extracting ceph user uid/gid from container image", 15),
            ("creating mon", 20),
            ("waiting for mon to start", 25),
            ("wrote config", 40),
            ("creating mgr", 45),
            ("waiting for mgr to start", 50),
            ("enabling cephadm module", 60),
            ("setting orchestrator backend to cephadm", 70),
            ("adding host", 80),
            ("bootstrap complete", 100),
        ]

        def outcb_handler(msg: str) -> None:
            if not percentcb:
                return
            t = msg.lower()
            for m, p in msg_to_percent:
                if m in t:
                    percentcb(p)

        def get_default_ceph_conf() -> str:
            s = ("[global]", "osd_pool_default_size = 2", "")
            return "\n".join(s)

        def write_tmp(s: str) -> IO[str]:
            t = tempfile.NamedTemporaryFile(
                prefix="aquarium-",
                mode="w",
            )
            t.write(s)
            t.flush()
            return t

        tmp_config: IO[str] = write_tmp(get_default_ceph_conf())
        cmd: List[str] = [
            "bootstrap",
            "--skip-pull",
            "--skip-prepare-host",
            "--mon-ip",
            addr,
            "--config",
            tmp_config.name,
            "--initial-dashboard-user",
            "admin",
            "--initial-dashboard-password",
            "aquarium",
            "--dashboard-password-noupdate",
            "--skip-monitoring-stack",
        ]
        return await self.call(cmd, noimage=False, outcb=outcb_handler)

    async def gather_facts(self) -> HostFactsModel:
        stdout, stderr, rc = await self.call(["gather-facts"], noimage=True)
        if rc != 0:
            raise CephadmError(stderr)
        try:
            return HostFactsModel.parse_raw(stdout)
        except pydantic.error_wrappers.ValidationError:
            raise CephadmError("format error while obtaining facts")

    async def get_volume_inventory(self) -> List[VolumeDeviceModel]:
        cmd = ["ceph-volume", "inventory", "--format", "json"]
        stdout, stderr, rc = await self.call(cmd)
        if rc != 0:
            raise CephadmError(stderr)
        try:
            devs = json.loads(stdout)
            logger.debug(json.dumps(devs, indent=2))
        except json.decoder.JSONDecodeError as e:
            raise CephadmError("format error while obtaining inventory") from e
        inventory = parse_obj_as(List[VolumeDeviceModel], devs)
        for d in inventory:
            if not d.human_readable_type:
                if d.sys_api.rotational:
                    d.human_readable_type = "hdd"
                else:
                    d.human_readable_type = "ssd"
        return inventory

    async def pull_images(self) -> None:
        logger.debug("fetching ceph container image")
        time_begin: int = int(time.monotonic())
        _, stderr, rc = await self.call(["pull"])
        if rc != 0:
            raise CephadmError(stderr)
        time_end: int = int(time.monotonic())
        time_diff: int = time_end - time_begin
        logger.debug(f"pulled ceph container images: took {time_diff} sec")
