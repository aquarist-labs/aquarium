# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from fastapi.routing import APIRouter
from pydantic import BaseModel
from typing import List

router: APIRouter = APIRouter(
    prefix="/orch",
    tags=["orch"]
)


class HostsReplyModel(BaseModel):
    hosts: List[str]


@router.get("/hosts", response_model=HostsReplyModel)
def get_hosts() -> HostsReplyModel:
    return HostsReplyModel(hosts=[])
