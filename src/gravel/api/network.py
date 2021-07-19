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

import logging
from typing import Dict, List
from fastapi import Depends, Request
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter

from gravel.api import jwt_auth_scheme
from gravel.controllers.resources.ifaces import (
    InterfaceModel,
    InterfaceStatsModel,
    Interfaces,
    NetworkCardModel,
)
from gravel.controllers.gstate import GlobalState

logger: logging.Logger = fastapi_logger
router = APIRouter(prefix="/network", tags=["network"])


@router.get("/cards", response_model=Dict[str, NetworkCardModel])
async def network_get_cards(
    request: Request, _=Depends(jwt_auth_scheme)
) -> Dict[str, NetworkCardModel]:
    """
    Obtain the node's network cards and associated interfaces.
    """
    gstate: GlobalState = request.app.state.gstate
    interfaces: Interfaces = gstate.interfaces
    return interfaces.cards


@router.get("/interfaces", response_model=Dict[str, InterfaceModel])
async def network_get_interfaces(
    request: Request, _=Depends(jwt_auth_scheme)
) -> Dict[str, InterfaceModel]:
    """
    Obtain the node's network interfaces, by name
    """
    gstate: GlobalState = request.app.state.gstate
    interfaces: Interfaces = gstate.interfaces
    return interfaces.interfaces


@router.get("/statistics", response_model=Dict[str, List[InterfaceStatsModel]])
async def network_get_statistics(
    request: Request, _=Depends(jwt_auth_scheme)
) -> Dict[str, List[InterfaceStatsModel]]:
    """
    Obtain the node's network interface statistics, by interface name
    """
    gstate: GlobalState = request.app.state.gstate
    interfaces: Interfaces = gstate.interfaces
    return interfaces.stats
