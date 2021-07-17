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

from __future__ import annotations
from typing import Awaitable, Callable
from gravel.cephadm.models import NodeInfoModel


class Subscriber:
    cb: Callable[[NodeInfoModel], Awaitable[None]]
    once: bool

    def __init__(
        self, cb: Callable[[NodeInfoModel], Awaitable[None]], once: bool
    ):
        # mypy is picking on type signature issues with the first argument of
        # the callable, while neither pyright nor visual inspection do. I'm
        # assuming this as one of mypy's quirks with Callables, and ignoring.
        self.cb = cb  # type: ignore
        self.once = once
