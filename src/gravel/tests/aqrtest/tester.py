#!/usr/bin/env python3
#
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

from __future__ import annotations
import os
import importlib
import sys
import asyncio
from pathlib import Path
from typing import Any, List, Tuple

from aqrtest.test import testlist


basedir = os.path.dirname(sys.argv[0])


def is_python(name: str) -> bool:
    return name.endswith(".py")


def get_module(parent: str, name: str) -> str:
    assert is_python(name)
    name = name[:name.rfind(".")]
    module = parent.replace("/", ".")
    return f"{module}.{name}"


def import_tests() -> None:
    for entry in os.walk(Path(basedir).joinpath("tests")):
        parent, _, filelst = entry
        if len(filelst) == 0:
            continue

        pyfiles = ((parent, f) for f in filelst if is_python(f))
        pymodules = (get_module(p, f) for p, f in pyfiles)

        for module in pymodules:
            print(f"=> {module}")
            try:
                importlib.import_module(module)
            except Exception as e:
                print(f"error: {str(e)}")
            else:
                print(f"=> imported {module}")


def perror(*args: Any, **kwargs: Any):
    print(*args, file=sys.stderr, **kwargs)


async def run_tests() -> bool:

    failed_tests: List[Tuple[str, List[str]]] = []
    num_tests: int = len(testlist)

    print(testlist)
    for name, testcls in testlist:
        print(f"=> RUN {name} ...")
        res, failures = await testcls.run()
        out = "PASSED" if res else "FAILED"
        print(f"=> RUN {name} ... {out}")
        if not res:
            failed_tests.append((name, failures))

    if len(failed_tests) > 0:
        perror("============ FAILURES ============")
        for testname, failures in failed_tests:
            perror(f"-------- [ {testname} ] -----------")
            if len(failures) == 0:
                perror("   NO FAILURES TO SHOW")
                continue

            failure_num = 1
            for failure in failures:
                perror(f"FAILURE #{failure_num}")
                perror(failure)
                perror(f"-- 8< -- END OF FAILURE #{failure_num} -- 8< --")
                failure_num += 1

    print(f"TOTAL TESTS: {num_tests}")
    print(f"     PASSED: {num_tests-len(failed_tests)}")
    print(f"     FAILED: {len(failed_tests)}")

    return len(failed_tests) == 0


if __name__ == "__main__":
    import_tests()
    success = asyncio.run(run_tests())
    if not success:
        sys.exit(1)
