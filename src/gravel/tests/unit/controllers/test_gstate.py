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

import asyncio
import pytest

from gravel.controllers.gstate import GlobalState


def test_gstate_inst(gstate: GlobalState):
    print(type(gstate))
    assert type(gstate).__name__ == "GlobalState"


@pytest.mark.asyncio
async def test_tickers(gstate: GlobalState):
    from gravel.controllers.gstate import Ticker

    class TestTicker(Ticker):
        def __init__(self):
            super().__init__(1.0)
            self.has_ticked = False

        async def _do_tick(self) -> None:
            self.has_ticked = True

        async def _should_tick(self) -> bool:
            return not self.has_ticked

    ticker = TestTicker()
    gstate.add_ticker("test", ticker)
    assert "test" in gstate._tickers

    await gstate._do_ticks()  # pyright: reportPrivateUsage=false
    await asyncio.sleep(1)  # let ticker tick
    assert ticker.has_ticked is True

    gstate.rm_ticker("test")
    assert "test" not in gstate._tickers

    ticker = TestTicker()
    gstate.add_ticker("test", ticker)
    assert "test" in gstate._tickers
    await gstate.start()
    await asyncio.sleep(1)  # let ticker tick
    await gstate.shutdown()
    assert ticker.has_ticked is True
