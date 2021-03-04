# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import asyncio
import pytest


def test_gstate_inst(fs, gstate):
    print(type(gstate))
    assert type(gstate).__name__ == 'GlobalState'


@pytest.mark.asyncio
async def test_tickers(gstate):
    from gravel.controllers.gstate import Ticker

    class TestTicker(Ticker):
        def __init__(self):
            super().__init__("test", 1.0)
            self.has_ticked = False

        async def _do_tick(self) -> None:
            self.has_ticked = True

        async def _should_tick(self) -> bool:
            return not self.has_ticked

    ticker = TestTicker()
    assert "test" in gstate.tickers.keys()

    await gstate._do_ticks()  # pyright: reportPrivateUsage=false
    await asyncio.sleep(1)  # let ticker tick
    assert ticker.has_ticked is True

    gstate.rm_ticker("test")
    assert "test" not in gstate.tickers

    ticker = TestTicker()
    assert "test" in gstate.tickers
    await gstate.start()
    await asyncio.sleep(1)  # let ticker tick
    await gstate.shutdown()
    assert ticker.has_ticked is True
