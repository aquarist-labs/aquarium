# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

import asyncio
import json
from enum import Enum
from fastapi.routing import APIRouter
from fastapi.logger import logger
from pydantic import BaseModel
from typing import Optional, List, Tuple, Dict, Any
from io import StringIO

from gravel.controllers.gstate import gstate
from gravel.cephadm.cephadm import Cephadm

router: APIRouter = APIRouter(
    prefix="/bootstrap",
    tags=["bootstrap"]
)


class NetworkAddressNotFoundError(Exception):
    pass


class BootstrapError(Exception):
    pass


class BootstrapStage(Enum):
    NONE = 0
    RUNNING = 1
    DONE = 2
    ERROR = 3


class Bootstrap:

    stage: BootstrapStage

    def __init__(self):
        self.stage = BootstrapStage.NONE
        pass

    async def bootstrap(self) -> bool:
        logger.debug("bootstrap > do bootstrap")

        selected_addr: Optional[str] = None
        
        try:
            selected_addr = await self._find_candidate_addr()
        except NetworkAddressNotFoundError as e:
            logger.error(f"unable to select network addr: {str(e)}")
            return False

        assert selected_addr
        logger.info(f"bootstrap > selected addr: {selected_addr}")

        try:
            asyncio.create_task(self._do_bootstrap(selected_addr))
        except Exception as e:
            logger.error(f"bootstrap > error starting bootstrap task: {str(e)}")
            return False

        return True


    async def get_stage(self) -> BootstrapStage:
        return self.stage


    async def _find_candidate_addr(self) -> str:
        logger.debug("bootstrap > find candidate address")

        stdout: str = ""
        stderr: str = ""
        retcode: int = 0

        try:
            cephadm: Cephadm = Cephadm()
            stdout, stderr, retcode = await cephadm.call("gather-facts")
        except Exception as e:
            raise NetworkAddressNotFoundError(e)

        if retcode != 0:
            logger.error("bootstrap > error obtaining host facts!")
            raise NetworkAddressNotFoundError("error obtaining host facts")
        
        hostinfo: Dict[str, Any] = {}
        try:
            hostinfo = json.loads(stdout)
        except Exception as e:
            raise NetworkAddressNotFoundError(e)

        if not hostinfo:
            logger.error("bootstrap > empty host facts!")
            raise NetworkAddressNotFoundError("unavailable host facts")

        if "interfaces" not in hostinfo:
            logger.error("bootstrap > unable to find interface facts!")
            raise NetworkAddressNotFoundError("interfaces not available")

        candidates: List[str] = []
        for iface, info in hostinfo["interfaces"].items():
            if info["iftype"] == "loopback":
                continue
            candidates.append(info["ipv4_address"])

        selected: Optional[str] = None
        if len(candidates) > 0:
            selected = candidates[0]

        if selected is None or len(selected) == 0:
            raise NetworkAddressNotFoundError("no address available")

        netmask_idx = selected.find("/")
        if netmask_idx > 0:
            selected = selected[:netmask_idx]

        return selected


    async def _do_bootstrap(self, selected_addr: str) -> None:
        logger.debug("bootstrap > run in background")
        assert selected_addr is not None and len(selected_addr) > 0
        self.stage = BootstrapStage.RUNNING

        stdout: str = ""
        stderr: str = ""
        retcode: int = 0
        try:
            cmd = f"bootstrap --skip-prepare-host --mon-ip {selected_addr}"
            cephadm: Cephadm = Cephadm()
            stdout, stderr, retcode = await cephadm.call(cmd)
        except Exception as e:
            raise BootstrapError(e)

        if retcode != 0:
            raise BootstrapError(f"error bootstrapping: rc = {retcode}")
        
        self.stage = BootstrapStage.DONE


class BasicReply(BaseModel):
    success: bool


class StatusReply(BaseModel):
    status: str


bootstrap = Bootstrap()


@router.post("/start")
async def start_bootstrap() -> BasicReply:
    res: bool = await bootstrap.bootstrap()
    return BasicReply(success=res)


@router.get("/status")
async def get_status() -> StatusReply:
    stage: BootstrapStage = await bootstrap.get_stage()
    stagestr: str = stage.name.lower()
    return StatusReply(status=stagestr)
