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
import multiprocessing
import traceback
from importlib import import_module
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from libaqua.errors import (
    AqrError,
    BoxDoesNotExistError,
    DeploymentExistsError
)
from libaqua.suites import SuiteEntry
from libaqua.deployment import Deployment
from libaqua.testing import (
    Requirements,
    TestCase,
    get_test_cases
)


class RunnerError(AqrError):
    pass


class CaseResult(BaseModel):
    failures: Dict[str, str] = Field({})
    results: List[Tuple[str, bool]] = Field([])


class RunnerResult(BaseModel):
    retcode: int = Field(0)
    _out: List[str] = Field([])
    _err: List[str] = Field([])
    cases: Dict[str, CaseResult] = {}

    @property
    def out(self) -> List[str]:
        return self._out

    @property
    def err(self) -> List[str]:
        return self._err

    def add_out(self, value: str) -> None:
        self._out.append(value)

    def add_err(self, value: str) -> None:
        self._err.append(value)


class Runner(multiprocessing.Process):

    _boxname: str
    _provider: str
    _test: SuiteEntry
    _run_name: Optional[str]
    _deployment: Optional[Deployment]
    _deployments_path: Path
    _queue: "multiprocessing.Queue[RunnerResult]"

    def __init__(
        self,
        deployments: Path,
        boxname: str,
        provider: str,
        test: SuiteEntry
    ):
        super().__init__()
        print(f"create runner for {test}")
        self._boxname = boxname
        self._provider= provider
        self._test = test
        self._deployment = None
        self._run_name = None
        self._deployments_path = deployments
        self._queue = multiprocessing.Queue()

    def run(self) -> None:
        result: RunnerResult = RunnerResult()

        try:
            import_module(self._test.module)
        except Exception as e:
            print(f"error: {str(e)}")
            result.retcode = 1
            result.add_err(str(e))
            self._queue.put(result)
            return

        test_cases: Dict[str, TestCase] = get_test_cases()
        has_failures = False
        for casename, case in test_cases.items():
            try:
                self._setup(case.requirements)
            except RunnerError as e:
                result.retcode = e.errno
                result.add_err(e.message)
                break

            try:
                asyncio.run(case.run())
            except Exception:
                result.retcode = 1
                result.add_err(traceback.format_exc())
            finally:
                try:
                    self._teardown()
                except RunnerError as e:
                    result.retcode = e.errno
                    result.add_err(e.message)
                    break

            case_result: CaseResult = CaseResult()
            case_result.failures = case.failures
            case_result.results = case.results
            result.cases[casename] = case_result
            if len(case.failures) > 0:
                has_failures = True

        result.retcode = 0 if not has_failures else 1
        self._queue.put(result)

    @property
    def result(self) -> RunnerResult:
        return self._queue.get()

    def _setup(self, requirements: Requirements) -> None:
        assert self._deployments_path.exists()

        def _gen_name() -> str:
            from datetime import datetime as dt
            now = dt.now().isoformat().replace(":", "").split(".")[0]
            return f"aqrtest-{self._test.name}-{now}"

        self._run_name = _gen_name()
        try:
            self._deployment = Deployment.create(
                name=self._run_name,
                box=self._boxname,
                provider=self._provider,
                num_nodes=requirements.nodes,
                num_disks=requirements.disks,
                num_nics=requirements.nics,
                deployments_path=self._deployments_path,
                mount_path=None
            )
        except FileNotFoundError as e:
            raise e
        except DeploymentExistsError as e:
            raise RunnerError(
                msg=f"deployment already exists for run '{self._run_name}",
                errno=e.errno
            )
        except BoxDoesNotExistError as e:
            raise RunnerError(
                msg=f"unable to find box '{self._boxname} for test",
                errno=e.errno
            )
        except AqrError as e:
            raise RunnerError(msg=e.message, errno=e.errno)

        try:
            self._deployment.start(conservative=False)
        except AqrError as e:
            raise RunnerError(
                msg=f"starting deployment: {e.message}",
                errno=e.errno
            )

    def _teardown(self) -> None:
        if not self._deployment:
            return
        try:
            self._deployment.stop(interactive=False)
            self._deployment.remove()
        except AqrError as e:
            raise RunnerError(
                msg=f"tearing down: {e.message}",
                errno=e.errno
            )
