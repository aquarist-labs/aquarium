# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import asyncio
from enum import Enum
from logging import Logger
from fastapi.logger import logger as fastapi_logger
from typing import Optional, List

from gravel.controllers.config import DeploymentStage
from gravel.controllers.gstate import gstate
from gravel.cephadm.cephadm import Cephadm
from gravel.controllers.nodes import get_node_mgr


logger: Logger = fastapi_logger  # required to provide type-hint to pylance


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

        try:
            cephadm: Cephadm = Cephadm()
            facts = await cephadm.gather_facts()
        except Exception as e:
            raise NetworkAddressNotFoundError(e)

        if len(facts.interfaces) == 0:
            logger.error("bootstrap > unable to find interface facts!")
            raise NetworkAddressNotFoundError("interfaces not available")

        candidates: List[str] = []

        for nic in facts.interfaces.values():
            if nic.iftype == "loopback":
                continue
            candidates.append(nic.ipv4_address)

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

        retcode: int = 0
        try:
            cephadm: Cephadm = Cephadm()
            _, _, retcode = await cephadm.bootstrap(selected_addr)
        except Exception as e:
            raise BootstrapError(e) from e

        if retcode != 0:
            raise BootstrapError(f"error bootstrapping: rc = {retcode}")

        self.stage = BootstrapStage.DONE
        gstate.config.set_deployment_stage(DeploymentStage.bootstrapped)
        await get_node_mgr().finish_bootstrap()
