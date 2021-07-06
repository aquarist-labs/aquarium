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

from typing import List, Optional
import pytest
from pytest_mock import MockerFixture
import asyncio


class FakeStreamReader:
    contents: str

    def __init__(self, contents: str) -> None:
        self.contents = contents

    async def read(self) -> bytes:
        return self.contents.encode("utf-8")

    async def readline(self) -> bytes:
        lines = self.contents.splitlines()
        return lines[0].encode("utf-8")


class FakeProcess:
    stderr: Optional[FakeStreamReader] = None
    stdout: Optional[FakeStreamReader] = None
    returncode: int

    def __init__(
        self, stdout: Optional[str], stderr: Optional[str], ret: int
    ) -> None:
        if stdout:
            self.stdout = FakeStreamReader(stdout)
        if stderr:
            self.stderr = FakeStreamReader(stderr)
        self.returncode = ret

    async def wait(self) -> int:
        return self.returncode


@pytest.mark.asyncio
async def test_aqr_run_cmd(mocker: MockerFixture) -> None:

    async def mock_subprocess(
        *args: List[str], stdout: int, stderr: int
    ) -> FakeProcess:
        assert args[0] == "foo"
        assert args[1] == "bar"
        assert stdout == asyncio.subprocess.PIPE
        assert stderr == asyncio.subprocess.PIPE
        return FakeProcess(stdout="mystdout", stderr="mystderr", ret=0)

    mocker.patch("asyncio.create_subprocess_exec", new=mock_subprocess)
    from gravel.controllers.utils import aqr_run_cmd
    ret, out, err = await aqr_run_cmd(["foo", "bar"])
    assert ret == 0
    assert out == "mystdout"
    assert err == "mystderr"
