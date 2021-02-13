# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from typing import Optional
from gravel import gstate
from gravel.cephadm.models import NodeInfoModel
from gravel.controllers.gstate import Ticker


class Inventory(Ticker):

    _latest: Optional[NodeInfoModel]

    def __init__(self):
        self.is_ticking = False
        self._latest = None
        gstate.add_ticker("inventory", self)

    async def tick(self) -> None:
        if self.is_ticking:
            return

        self.is_ticking = True

        self.is_ticking = False
        pass

    async def latest(self) -> Optional[NodeInfoModel]:
        return self._latest
