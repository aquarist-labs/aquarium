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

import requests

from aqrtest.test import AqrTest, test


@test("test orch devices")
class TestOrchDevices(AqrTest):

    async def run_test(self) -> bool:
        print("run test 1")
        try:
            res = requests.get(
                "http://127.0.0.1:1337/api/orch/devices",
                timeout=1)
            print(f"res: {res}")
        except Exception:
            return False
        return True


@test("test function")
async def testfunc() -> bool:
    return True
