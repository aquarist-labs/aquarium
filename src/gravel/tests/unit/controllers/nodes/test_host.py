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

# pyright: reportUnknownMemberType=false, reportMissingTypeStubs=false

import os
from typing import Callable, List, Optional, Tuple
import pytest
from pytest_mock import MockerFixture
from pyfakefs import fake_filesystem


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.mark.asyncio
async def test_set_hostname(
    mocker: MockerFixture,
    fs: fake_filesystem.FakeFilesystem,
    get_data_contents: Callable[[str, str], str],
) -> None:

    called_set_hostname = False

    async def mock_call(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        nonlocal called_set_hostname
        called_set_hostname = True
        assert cmd[0] == "hostnamectl"
        assert cmd[1] == "set-hostname"
        assert cmd[2] == "foobar"
        return 0, None, None

    async def mock_call_fail(
        cmd: List[str],
    ) -> Tuple[int, Optional[str], Optional[str]]:
        return 1, None, "oops"

    from gravel.controllers.nodes.host import set_hostname, HostnameCtlError

    mocker.patch("socket.gethostname", return_value="myhostname")

    mocker.patch(
        "gravel.controllers.nodes.host.aqr_run_cmd", new=mock_call_fail
    )
    throws = False
    try:
        await set_hostname("foobar")
    except HostnameCtlError as e:
        assert "oops" in e.message
        throws = True
    assert throws
    assert not fs.exists("/etc/hosts")

    mocker.patch("gravel.controllers.nodes.host.aqr_run_cmd", new=mock_call)
    fs.create_file("/etc/hosts")
    hosts = get_data_contents(DATA_DIR, "hosts.raw")
    with open("/etc/hosts", "w") as f:
        f.write(hosts)

    await set_hostname("foobar")
    assert called_set_hostname
    with open("/etc/hosts", "r") as f:
        text = f.read()
        assert text.count("myhostname") == 0
        assert text.count("foobar") == 2
