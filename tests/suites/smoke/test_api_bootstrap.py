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


@requirements(
    disks=4,
    nodes=1,
    nics=1
)
class TestAPIBootstrap(TestCase):

    @caseunit
    async def test_func_1(self):
        print("running test func 1")
        assert True

    @caseunit
    async def test_func_2(self):
        print("running test func 2")
        assert True
