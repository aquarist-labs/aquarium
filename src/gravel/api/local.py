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

from logging import Logger
from typing import List
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter
from fastapi import HTTPException, status

from gravel.cephadm.cephadm import Cephadm
from gravel.cephadm.models import (
    NodeInfoModel,
    VolumeDeviceModel
)
from gravel.controllers.resources import inventory


logger: Logger = fastapi_logger

router: APIRouter = APIRouter(
    prefix="/local",
    tags=["local"]
)


@router.get(
    "/volumes",
    name="Obtain local volumes",
    response_model=List[VolumeDeviceModel]
)
async def get_volumes() -> List[VolumeDeviceModel]:
    """
    List this node's volumes.

    This information is obtained via `cephadm`, periodically, and may not be
    100% up to date between calls to this endpoint.
    """
    latest = inventory.get_inventory().latest
    if not latest:
        raise HTTPException(status_code=status.HTTP_425_TOO_EARLY,
                            detail="Volume list not yet available")
    return latest.disks


@router.get(
    "/nodeinfo",
    name="Obtain local node information",
    response_model=NodeInfoModel
)
async def get_node_info() -> NodeInfoModel:
    """
    Obtain this node's information and facts.

    Lists the node's volumes (same as `/local/volumes`), and additional host
    information, such as OS metadata, NICs, etc.

    This information is obtained via `cephadm`.

    This is a sync call to `cephadm` and may take a while to return.
    """
    cephadm = Cephadm()
    return await cephadm.get_node_info()


@router.get(
    "/inventory",
    name="Obtain local node inventory",
    response_model=NodeInfoModel
)
async def get_inventory() -> NodeInfoModel:
    """
    Obtain this node's inventory.

    Includes information about the node's devices, OS information, NICs, etc.

    This information is obtained via `cephadm`, periodically, and may not be
    100% up to date between calls to this endpoint.

    This endpoint is preferred over `/local/nodeinfo` because the information
    is cached and puts less strain on the node. If the most up to date
    information is required, and the caller does not have constraints waiting
    for a return, `/local/nodeinfo` should be used.
    """
    latest = inventory.get_inventory().latest
    if not latest:
        raise HTTPException(status_code=status.HTTP_425_TOO_EARLY,
                            detail="Inventory not available")
    return latest
