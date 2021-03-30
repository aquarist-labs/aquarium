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
from typing import Dict
from fastapi.logger import logger as fastapi_logger
from fastapi.routing import APIRouter

from gravel.controllers.resources.devices import (
    DeviceHostModel,
    get_devices
)

logger: Logger = fastapi_logger

router: APIRouter = APIRouter(
    prefix="/devices",
    tags=["devices"]
)


@router.get(
    "/",
    name="Obtain devices being used for storage, per host",
    response_model=Dict[str, DeviceHostModel]
)
def get_per_host_devices() -> Dict[str, DeviceHostModel]:
    return get_devices().devices_per_host
