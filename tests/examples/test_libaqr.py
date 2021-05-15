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

import asyncio
from libaqr.testing import TestCase, caseunit, get_test_cases, requirements


@requirements(disks=1, nics=6)
class MyTest(TestCase):

    @caseunit
    async def func1(self):
        print("mytest func1")

    async def not_a_unit(self):
        raise Exception("not a unit")

    @caseunit
    async def func2(self):
        print("mytest func2")
        raise Exception("bar")


@requirements
async def func2():
    print("func 2")
    raise Exception("foo")


@requirements(disks=1, nics=1, nodes=1)
async def func3():
    print("func 3")


async def main() -> None:

    tests = get_test_cases()
    for casename, case in tests.items():
        print(f"=> {casename}")
        print(f"   reqs: {case.requirements}")
        print(f"  units: {len(case.get_units())}")
        await case.run()

        has_failures = False
        print("   -- results --")
        for testname, result in case.results:
            print(f"   {testname}: {result}")
            if not result:
                has_failures = True

        if has_failures:
            print("   -- failures --")
            for testname, failurestr in case.failures.items():
                print(f"   unit: {testname}")
                print(failurestr)


if __name__ == "__main__":
    asyncio.run(main())
