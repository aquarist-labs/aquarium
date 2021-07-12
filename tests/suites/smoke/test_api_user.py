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
class TestAPIUser(TestCase):

    @caseunit
    async def fail_update_user(self) -> None:
        async with conn() as session:
            res = await session.post(
                "/user/create",
                json={
                    "username": "foo",
                    "password": "1234",
                    "full_name": "Foo Buz",
                    "disabled": False
                }
            )
            assert res.status == 200

            res = await session.patch(
                "/user/foo",
                json={
                    "username": "foo",
                    "password": "",
                    "full_name": "Foo Bar",
                    "disabled": True
                }
            )
            assert res.status == 400
