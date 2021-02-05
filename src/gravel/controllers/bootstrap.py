# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import asyncio
import json
from enum import Enum
from fastapi.logger import logger
from typing import Optional, List, Dict, Any

from gravel.controllers.config import DeploymentStage
from gravel.controllers.gstate import gstate
from gravel.cephadm.cephadm import Cephadm


class NetworkAddressNotFoundError(Exception):
    pass


class BootstrapError(Exception):
    pass


class BootstrapStage(str, Enum):
    NONE = "none"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class Bootstrap:

    stage: BootstrapStage

    def __init__(self):
        self.stage = BootstrapStage.NONE
        pass

    async def _should_bootstrap(self) -> bool:
        state: DeploymentStage = gstate.config.deployment_state.stage
        if state == DeploymentStage.none or \
           state == DeploymentStage.bootstrapping:
            return True
        return False

    async def _is_bootstrapping(self) -> bool:
        state: DeploymentStage = gstate.config.deployment_state.stage
        return state == DeploymentStage.bootstrapping

    async def bootstrap(self) -> bool:
        logger.debug("bootstrap > do bootstrap")

        if not await self._should_bootstrap():
            return False

        if await self._is_bootstrapping():
            return True

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
        gstate.config.set_deployment_stage(DeploymentStage.bootstrapping)

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
        gstate.config.set_deployment_stage(DeploymentStage.bootstrapped)
