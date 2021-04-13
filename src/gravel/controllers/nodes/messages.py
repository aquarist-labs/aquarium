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

from enum import Enum
from uuid import UUID
from typing import Any

from pydantic import BaseModel


class MessageTypeEnum(int, Enum):
    ERROR = 0
    JOIN = 1
    WELCOME = 2
    READY_TO_ADD = 3


class MessageModel(BaseModel):
    type: MessageTypeEnum
    data: Any


class JoinMessageModel(BaseModel):
    uuid: UUID
    hostname: str
    address: str
    token: str


class WelcomeMessageModel(BaseModel):
    pubkey: str
    cephconf: str
    keyring: str
    etcd_peer: str


class ReadyToAddMessageModel(BaseModel):
    pass


class ErrorMessageModel(BaseModel):
    what: str
    code: int
