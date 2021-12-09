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

# pyright: reportPrivateUsage=false, reportMissingTypeStubs=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false

import pytest
from pyfakefs import fake_filesystem

from gravel.controllers.gstate import GlobalState
from gravel.controllers.nodes.mgr import NodeMgr


@pytest.fixture
def nodemgr(gstate: GlobalState) -> NodeMgr:  # type: ignore

    from gravel.controllers.nodes.mgr import NodeStateModel

    nodemgr = NodeMgr(gstate)
    nodemgr._state = NodeStateModel(
        uuid="bba35d93-d4a5-48b3-804b-99c406555c89",
        address="1.2.3.4",
        hostname="foobar",
    )
    yield nodemgr


def test_fail_init(
    gstate: GlobalState, fs: fake_filesystem.FakeFilesystem
) -> None:

    from gravel.controllers.nodes.mgr import NodeError

    if fs.exists("/etc/aquarium/node.json"):
        fs.remove("/etc/aquarium/node.json")
    fs.create_dir("/etc/aquarium/node.json")
    throws = False
    nodemgr = NodeMgr(gstate)
    try:
        nodemgr.init()
    except NodeError:
        throws = True
    except Exception:
        assert False
    assert throws
    # clean up
    fs.rmdir("/etc/aquarium/node.json")


def test_init(gstate: GlobalState, fs: fake_filesystem.FakeFilesystem) -> None:

    nodemgr = NodeMgr(gstate)
    nodemgr.init()
    assert fs.exists("/etc/aquarium/node.json")

    # clean up
    for f in fs.listdir("/etc/aquarium"):
        fs.remove(f"/etc/aquarium/{f}")
