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

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel


class AqrTestError(Exception):

    _msg: str

    def __init__(self, message: str = ""):
        super().__init__()
        self._msg = message

    @property
    def message(self) -> str:
        return self._msg


class MissingSuiteNameError(AqrTestError):
    pass


class NoSuchSuiteError(AqrTestError):
    pass


class SuiteEntry(BaseModel):
    suite: str
    suite_path: Path
    name: str
    path: Path
    module: str

    @property
    def test_name(self) -> str:
        return f"{self.suite}/{self.name}"


def get_available_suites(path: Path) -> List[str]:
    return next(os.walk(path))[1]


def get_suite_entries(
    path: Path,
    suite: str,
    test_name: Optional[str]
):
    suites_path = path.joinpath(suite)
    if not suites_path.exists():
        raise NoSuchSuiteError(suite)

    tests = next(os.walk(suites_path))[2]
    for test in tests:
        if not test.endswith(".py") and not test.startswith("test_"):
            continue

        entry_name = test.replace(".py", "")

        if test_name and test_name != entry_name:
            continue

        entry_path = suites_path.joinpath(test)
        entry_module = f"suites.{suite}.{entry_name}"

        sentry = SuiteEntry(
            suite=suite,
            suite_path=suites_path,
            name=entry_name,
            path=entry_path,
            module=entry_module
        )
        yield sentry


def get_suite_tests(
    path: Path,
    suite_name: Optional[str],
    test_name: Optional[str]
):

    if test_name and not suite_name:
        pos = test_name.find("/")
        if pos >= 0:
            suite_name = test_name[:pos]
            test_name = test_name[pos+1:]
        else:
            raise MissingSuiteNameError()

    available = get_available_suites(path)
    for suite in available:

        if suite_name and suite != suite_name:
            continue

        for entry in get_suite_entries(path, suite, test_name):
            yield entry
