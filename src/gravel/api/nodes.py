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
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

from gravel.api import install_gate, jwt_auth_scheme
from gravel.controllers.nodes.disks import Disks, DiskSolution
from gravel.controllers.nodes.mgr import NodeMgr

logger: Logger = fastapi_logger
router = APIRouter(prefix="/nodes", tags=["nodes"])


class SetHostnameRequest(BaseModel):
    name: str = Field(min_length=1, title="The system hostname")


@router.get("/deployment/disksolution", response_model=DiskSolution)
async def node_get_disk_solution(
    request: Request,
    jwt: Any = Depends(jwt_auth_scheme),
    gate: Any = Depends(install_gate),
) -> DiskSolution:
    """
    Obtain the list of disks and a deployment solution, if possible.
    """
    logger.debug("api > nodes > deployment > devices")
    nodemgr: NodeMgr = request.app.state.nodemgr

    if not nodemgr.available:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Node is not available.",
        )

    return Disks.gen_solution(request.app.state.gstate)
