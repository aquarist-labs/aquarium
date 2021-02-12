# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import asyncio
import os
import json
from io import StringIO
from typing import List, Tuple

import pydantic
from pydantic.tools import parse_obj_as

from .models import HostFactsModel, NodeCPUInfoModel, \
    NodeCPULoadModel, NodeInfoModel, NodeMemoryInfoModel, \
    VolumeDeviceModel


class CephadmError(Exception):
    pass


class Cephadm:

    def __init__(self):

        if os.path.exists("./gravel/cephadm/cephadm.bin"):
            # dev environment
            self.cephadm = "sudo ./gravel/cephadm/cephadm.bin"
        else:
            # deployment environment
            self.cephadm = "sudo cephadm"

        pass

    async def call(self, cmd: str) -> Tuple[str, str, int]:

        cmdlst: List[str] = f"{self.cephadm} {cmd}".split()

        process = await asyncio.create_subprocess_exec(
            *cmdlst,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        assert process.stdout
        assert process.stderr

        stdout, stderr = await asyncio.gather(
            self._tee(process.stdout), self._tee(process.stderr)
        )
        retcode = await asyncio.wait_for(process.wait(), None)

        return stdout, stderr, retcode

    async def run_in_background(self, cmd: List[str]) -> None:
        pass

    async def _tee(self, reader: asyncio.StreamReader) -> str:
        collected = StringIO()
        async for line in reader:
            msg = line.decode("utf-8")
            collected.write(msg)
        return collected.getvalue()

    #
    # command wrappers
    #

    async def bootstrap(self, addr: str) -> Tuple[str, str, int]:

        if not addr:
            raise CephadmError("address not specified")

        cmd = f"bootstrap --skip-prepare-host --mon-ip {addr}"
        return await self.call(cmd)

    async def gather_facts(self) -> HostFactsModel:
        stdout, stderr, rc = await self.call("gather-facts")
        if rc != 0:
            raise CephadmError(stderr)
        try:
            return HostFactsModel.parse_raw(stdout)
        except pydantic.error_wrappers.ValidationError:
            raise CephadmError("format error while obtaining facts")

    async def get_volume_inventory(self) -> List[VolumeDeviceModel]:
        cmd = "ceph-volume inventory --format=json"
        stdout, stderr, rc = await self.call(cmd)
        if rc != 0:
            raise CephadmError(stderr)
        try:
            devs = json.loads(stdout)
            print(json.dumps(devs, indent=2))
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

    async def get_node_info(self) -> NodeInfoModel:
        try:
            facts = await self.gather_facts()
            inventory = await self.get_volume_inventory()
        except CephadmError as e:
            raise CephadmError("error obtaining node info") from e

        return NodeInfoModel(
            hostname=facts.hostname,
            model=facts.model,
            vendor=facts.vendor,
            kernel=facts.kernel,
            operating_system=facts.operating_system,
            system_uptime=facts.system_uptime,
            current_time=facts.timestamp,
            cpu=NodeCPUInfoModel(
                model=facts.cpu_model,
                cores=facts.cpu_cores,
                count=facts.cpu_count,
                threads=facts.cpu_threads,
                load=NodeCPULoadModel(
                    one_min=facts.cpu_load["1min"],
                    five_min=facts.cpu_load["5min"],
                    fifteen_min=facts.cpu_load["15min"]
                )
            ),
            nics=facts.interfaces,
            memory=NodeMemoryInfoModel(
                available_kb=facts.memory_available_kb,
                free_kb=facts.memory_free_kb,
                total_kb=facts.memory_total_kb
            ),
            disks=inventory
        )
