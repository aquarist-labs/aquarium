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
from fastapi import (
    APIRouter
)

from gravel.controllers.events import (
    EventMessageModel,
    get_events_ctrl
)


logger: Logger = fastapi_logger

router: APIRouter = APIRouter(
    prefix="/events",
    tags=["events"]
)


@router.get(
    "/",
    name="Obtain latest events",
    response_model=List[EventMessageModel]
)
async def get_events() -> List[EventMessageModel]:
    events_ctrl = get_events_ctrl()
    return events_ctrl.events
