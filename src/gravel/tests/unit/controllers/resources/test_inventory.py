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

# pyright: reportPrivateUsage=false

import os
from typing import Callable
import pytest
from pytest_mock import MockerFixture

from gravel.cephadm.models import NodeInfoModel
from gravel.controllers.gstate import GlobalState
from gravel.controllers.resources.inventory import Inventory


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.mark.asyncio
async def test_inventory_subs(
    mocker: MockerFixture,
    gstate: GlobalState,
    get_data_contents: Callable[[str, str], str],
):

    nodeinfo: NodeInfoModel = NodeInfoModel.parse_raw(
        get_data_contents(DATA_DIR, "inventory_basic.json")
    )

    inventory: Inventory = gstate.inventory
    inventory._latest = nodeinfo
    prev_subs = inventory._subscribers
    inventory._subscribers = []

    num_called: int = 0

    async def cb(info: NodeInfoModel) -> None:
        nonlocal num_called
        num_called += 1
        assert info == nodeinfo
        pass

    assert inventory._latest
    sub = await inventory.subscribe(cb=cb, once=True)
    assert not sub
    assert num_called == 1

    sub = await inventory.subscribe(cb=cb, once=False)
    assert sub is not None
    assert sub in inventory._subscribers
    assert num_called == 2

    await inventory._publish()
    assert num_called == 3

    inventory.unsubscribe(sub)
    assert sub not in inventory._subscribers

    # cleanup
    inventory._subscribers = prev_subs
