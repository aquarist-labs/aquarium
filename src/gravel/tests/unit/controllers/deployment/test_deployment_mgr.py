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

# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
# pyright: reportMissingTypeStubs=false

import pytest
from pyfakefs import fake_filesystem
from pytest_mock import MockerFixture


def test_instance() -> None:
    from gravel.controllers.deployment.mgr import (
        DeploymentMgr,
        DeploymentStateEnum,
        InitStateEnum,
    )

    mgr = DeploymentMgr()
    assert mgr._init_state == InitStateEnum.NONE
    assert mgr._deployment_state == DeploymentStateEnum.NONE
    assert not mgr._preinited
    assert not mgr._inited


@pytest.mark.asyncio
async def test_preinit_fails() -> None:
    from gravel.controllers.deployment.mgr import (
        AlreadyInitedError,
        AlreadyPreInitedError,
        DeploymentMgr,
    )

    raised: bool = False
    mgr = DeploymentMgr()
    mgr._preinited = True
    try:
        await mgr.preinit()
    except AlreadyPreInitedError:
        raised = True
    except Exception:
        assert False
    assert raised

    raised = False
    mgr = DeploymentMgr()
    mgr._inited = True
    try:
        await mgr.preinit()
    except AlreadyInitedError:
        raised = True
    except Exception:
        assert False
    assert raised


@pytest.mark.asyncio
async def test_preinit(mocker: MockerFixture) -> None:
    from gravel.controllers.deployment.mgr import (
        DeploymentError,
        DeploymentMgr,
        InitStateEnum,
    )
    from gravel.controllers.nodes.systemdisk import OverlayError

    mgr: DeploymentMgr = DeploymentMgr()
    mocker.patch(
        "gravel.controllers.nodes.systemdisk.SystemDisk.exists",
        new=mocker.AsyncMock(return_value=False),
    )
    await mgr.preinit()
    assert mgr._preinited == True
    assert mgr._init_state == InitStateEnum.NONE

    mgr = DeploymentMgr()
    mocker.patch(
        "gravel.controllers.nodes.systemdisk.SystemDisk.exists",
        new=mocker.AsyncMock(return_value=True),
    )
    mocker.patch(
        "gravel.controllers.nodes.systemdisk.SystemDisk.enable",
        new=mocker.AsyncMock(side_effect=OverlayError),
    )

    raised = False
    try:
        await mgr.preinit()
    except DeploymentError:
        raised = True
    except Exception:
        assert False
    assert raised
    assert not mgr._preinited
    assert mgr._init_state == InitStateEnum.NONE

    mgr = DeploymentMgr()
    mocker.patch(
        "gravel.controllers.nodes.systemdisk.SystemDisk.enable",
        new=mocker.AsyncMock(),
    )

    await mgr.preinit()
    assert mgr._preinited
    assert mgr._init_state == InitStateEnum.INSTALLED


@pytest.mark.asyncio
async def test_init(fs: fake_filesystem.FakeFilesystem) -> None:

    from gravel.controllers.deployment.mgr import (
        AlreadyInitedError,
        DeploymentMgr,
        InitError,
        InitStateEnum,
        NotPreInitedError,
    )

    mgr = DeploymentMgr()

    raised: bool = False
    try:
        await mgr.init()
    except NotPreInitedError:
        raised = True
    except Exception:
        assert False
    assert raised

    mgr._preinited = True
    mgr._inited = True
    raised = False
    try:
        await mgr.init()
    except AlreadyInitedError:
        raised = True
    except Exception:
        assert False
    assert raised

    mgr._preinited = True
    mgr._inited = False
    await mgr.init()  # succeeds because we're not installed yet.
    assert mgr._init_state < InitStateEnum.INSTALLED

    # test canonical case, we're installed but don't have a state yet.
    fs.reset()
    mgr = DeploymentMgr()
    mgr._preinited = True
    mgr._inited = False
    mgr._init_state = InitStateEnum.INSTALLED

    assert not fs.exists("/etc/aquarium")
    await mgr.init()
    assert mgr._inited
    assert fs.exists("/etc/aquarium/")
    assert fs.isdir("/etc/aquarium")
    assert fs.exists("/etc/aquarium/state.json")

    # ensure we have a malformed file in /etc/aquarium/state.json
    fs.reset()
    mgr = DeploymentMgr()
    mgr._preinited = True
    mgr._inited = False
    mgr._init_state = InitStateEnum.INSTALLED

    fs.create_dir("/etc/aquarium")
    with open("/etc/aquarium/state.json", "w") as f:
        f.write("foobarbaz")

    raised = False
    try:
        await mgr.init()
    except InitError:
        raised = True
    except Exception:
        assert False
    assert raised

    # now we have something in state.json that is not a file
    fs.reset()
    mgr = DeploymentMgr()
    mgr._preinited = True
    mgr._inited = False
    mgr._init_state = InitStateEnum.INSTALLED

    fs.create_dir("/etc/aquarium/state.json")
    raised = False
    try:
        await mgr.init()
    except InitError:
        raised = True
    except Exception:
        assert False
    assert raised
