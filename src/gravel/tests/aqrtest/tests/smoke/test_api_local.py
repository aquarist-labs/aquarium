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
from aiohttp import ClientSession, ClientResponse

from aqrtest.test import test, httptest

from gravel.controllers.resources.inventory import NodeInfoModel


async def _get(session: ClientSession, what: str) -> ClientResponse:
    return await session.get(
        f"http://localhost:1337/api/local/{what}"
    )


async def _get_inventory(session: ClientSession) -> ClientResponse:
    return await _get(session, "inventory")


async def _wait_inventory(session: ClientSession) -> bool:
    inited = False
    for _ in range(30):
        async with await _get(session, "status") as req:
            assert req.status == 200
            res = await req.json()
            if "inited" in res and res["inited"]:
                inited = True
                break
            await asyncio.sleep(1)
    return inited


@test("fail get local inventory")
@httptest
async def test_local_inventory(session: ClientSession) -> bool:

    req = await _get_inventory(session)
    assert req.status == 425
    res = await req.json()
    assert "detail" in res
    assert "not available" in res["detail"]
    return True


@test("wait and get local inventory")
@httptest
async def test_wait_get_local_inventory(session: ClientSession) -> bool:

    res = await _wait_inventory(session)
    assert res
    req = await _get_inventory(session)
    assert req.status == 200
    return True


@test("check inventory")
@httptest
async def test_check_inventory(session: ClientSession) -> bool:
    res = await _wait_inventory(session)
    assert res
    req = await _get_inventory(session)
    assert req.status == 200
    inventory = NodeInfoModel.parse_obj(await req.json())

    # min default for testing: 4 disks, 1 nic, 1 cpu thread
    assert len(inventory.disks) >= 4
    assert len(inventory.nics) >= 1
    assert inventory.cpu.threads >= 1

    # 1 disk unavailable (os disk), others available
    avail_disks = len([d for d in inventory.disks if d.available])
    assert avail_disks == (len(inventory.disks) - 1)

    return True
