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
import time
import subprocess
import shlex
from pathlib import Path
from typing import Optional
from libaqr.errors import AqrError, BoxDoesNotExistError, DeploymentExistsError
from libaqr.suites import SuiteEntry
from libaqr.deployment import Deployment


class RunnerError(AqrError):
    pass


class Runner:

    _boxname: str
    _test: SuiteEntry
    _run_name: Optional[str]
    _deployment: Optional[Deployment]

    def __init__(self, boxname: str, test: SuiteEntry):
        print(f"create runner for {test}")
        self._boxname = boxname
        self._test = test
        self._deployment = None
        self._run_name = None

    def run(self) -> bool:
        assert self._deployment
        assert self._run_name
        print(f"running test {self._test}, run {self._run_name}")
        start = int(time.monotonic())

        cmd = f"python3 {str(self._test.path)}"
        env = os.environ.copy()
        pythonpath = str(Path(os.path.dirname(__file__)).parent)
        env["PYTHONPATH"] = pythonpath
        success = True
        try:
            proc = subprocess.run(
                shlex.split(cmd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            if proc.returncode != 0:
                success = False
                print(f"test error:\n{proc.stderr.decode('utf-8')}")
                # dump stderr / stdout to file
        except Exception as e:
            success = False
            print(f"error: {str(e)}")

        stop = int(time.monotonic())
        diff = stop - start
        status_str = "passed" if success else "failed"
        print(f"test took {diff} seconds: {status_str}")
        return success

    def setup(self, deployments_path: Path) -> None:
        assert deployments_path.exists()

        def _gen_name() -> str:
            from datetime import datetime as dt
            now = dt.now().isoformat().replace(":", "").split(".")[0]
            return f"aqrtest-{self._test.name}-{now}"

        self._run_name = _gen_name()
        try:
            self._deployment = Deployment.create(
                name=self._run_name,
                box=self._boxname,
                num_nodes=2, num_disks=4, num_nics=1,
                deployments_path=deployments_path,
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

    def teardown(self) -> None:
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
