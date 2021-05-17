# project aquarium's testing battery
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

from libaqr.testing import TestCase, caseunit, requirements
from libaqr.http import conn


@requirements(
    disks=1,
    nodes=1,
    nics=1
)
class ExpectFailAPIOrch(TestCase):

    @caseunit
    async def fail_hosts(self) -> None:
        async with conn() as session:
            res = await session.get("/orch/hosts", timeout=5)
            assert res.status != 200

    @caseunit
    async def fail_devices(self) -> None:
        async with conn() as session:
            res = await session.get("/orch/devices", timeout=5)
            assert res.status != 200

    @caseunit
    async def fail_devices_assimilate(self) -> None:
        async with conn() as session:
            res = await session.post(
                "/orch/devices/assimilate",
                json={},
                timeout=5
            )
            assert res.status != 200

            res = await session.get("/orch/devices/all_assimilated", timeout=5)
            assert res.status != 200

    @caseunit
    async def fail_pubkey(self) -> None:
        async with conn() as session:
            res = await session.get("/orch/pubkey", timeout=5)
            assert res != 200
