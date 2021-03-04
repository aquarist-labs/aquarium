# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from typing import Any
import unittest
import unittest.mock
import asyncio


class TestGlobalState(unittest.IsolatedAsyncioTestCase):  # type: ignore

    @unittest.mock.patch("gravel.controllers.config.Config")
    def test_gstate_inst(self, config_mock: Any):
        import gravel.controllers.config
        self.assertIs(gravel.controllers.config.Config, config_mock)
        from gravel.controllers.gstate import GlobalState
        GlobalState()

    @unittest.mock.patch("gravel.controllers.config.Config")
    async def test_tickers(self, config_mock: Any):

        from gravel.controllers.gstate import Ticker, gstate

        class TestTicker(Ticker):
            def __init__(self):
                super().__init__("test", 1.0)
                self.has_ticked = False

            async def _do_tick(self) -> None:
                self.has_ticked = True

            async def _should_tick(self) -> bool:
                return not self.has_ticked

        ticker = TestTicker()
        self.assertIn("test", gstate.tickers)

        await gstate._do_ticks()  # pyright: reportPrivateUsage=false
        await asyncio.sleep(1)  # let ticker tick
        self.assertTrue(ticker.has_ticked)

        gstate.rm_ticker("test")
        self.assertNotIn("test", gstate.tickers)

        ticker = TestTicker()
        self.assertIn("test", gstate.tickers)
        await gstate.start()
        await asyncio.sleep(1)  # let ticker tick
        await gstate.shutdown()
        self.assertTrue(ticker.has_ticked)
