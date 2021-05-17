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


from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Type, Union, cast
from pydantic import BaseModel, Field
import inspect
import traceback


class Requirements(BaseModel):
    disks: int = Field(4, description="number of disks")
    nics: int = Field(1, description="number of network interfaces")
    nodes: int = Field(2, description="number of nodes")


UnitCaseType = Callable[..., Awaitable[None]]


class TestCase:
    _requirements: Requirements
    _results: List[Tuple[str, bool]]
    _failures: Dict[str, str]

    def __init__(self) -> None:
        self._requirements = Requirements()
        self._results = []
        self._failures = {}

    @property
    def requirements(self) -> Requirements:
        return self._requirements

    @requirements.setter
    def requirements(self, reqs: Requirements) -> None:
        self._requirements = reqs

    @property
    def results(self) -> List[Tuple[str, bool]]:
        return self._results

    @property
    def failures(self) -> Dict[str, str]:
        return self._failures

    def get_units(self) -> List[Tuple[str, Any]]:
        _units: List[Tuple[str, Any]] = []
        lst = inspect.getmembers(self, predicate=inspect.iscoroutinefunction)
        for name, fn in lst:
            if hasattr(fn, "is_caseunit") and fn.is_caseunit:
                caseunit_name = fn.caseunit_name
                if not caseunit_name:
                    caseunit_name = name
                _units.append((caseunit_name, fn))
        return _units

    async def run(self) -> None:
        for name, fn in self.get_units():
            success = True
            try:
                await fn()
            except Exception:
                success = False
                self._failures[name] = traceback.format_exc()

            self._results.append((name, success))


_cases: Dict[str, TestCase] = {}


def get_test_cases() -> Dict[str, TestCase]:
    return _cases


def maybe_with_args(func: Any):
    def _wrapper(*args: Any, **kwargs: Any):
        if len(args) == 1 and callable(args[0]):
            return func(args[0])

        def _with_args(decoratee: Any):
            return func(decoratee, *args, **kwargs)
        return _with_args

    return _wrapper


@maybe_with_args
def requirements(
    _test: Union[Type[TestCase], UnitCaseType],
    disks: int = 4,
    nics: int = 1,
    nodes: int = 2
):

    reqs = Requirements(
        disks=disks,
        nics=nics,
        nodes=nodes
    )

    casename = _test.__qualname__
    print(f"case {casename}: {reqs=}")

    if inspect.isclass(_test):
        # ignore type because we still want to check this at runtime, but
        # not getting pyright's warning about unecessary is instance checking.
        if not issubclass(_test, TestCase):  # type: ignore
            raise TypeError(f"{_test} is a class not of type TestCase")
        testcls = cast(Type[TestCase], _test)

        if casename not in _cases:
            _cases[casename] = testcls()
        _cases[casename].requirements = reqs

        return testcls

    elif inspect.iscoroutinefunction(_test):
        coro = cast(Callable[..., Awaitable[None]], _test)

        assert casename not in _cases

        class TestCaseWrapper(TestCase):
            @caseunit(_test.__qualname__)
            async def testcase(self):
                await coro()

        testcls = TestCaseWrapper()
        testcls.requirements = reqs
        _cases[casename] = testcls
        return _cases[casename]
    else:
        raise TypeError("expected class or coro")


@maybe_with_args
def caseunit(_test: UnitCaseType, casename: Optional[str] = None):
    # these may report type errors depending on static checker, because these
    # are not known members of said function. So we'll ignore them because we
    # know what we are doing.
    _test.is_caseunit = True  # type: ignore
    _test.caseunit_name = _test.__qualname__  # type: ignore
    if casename:
        _test.caseunit_name = casename  # type: ignore
    return _test
