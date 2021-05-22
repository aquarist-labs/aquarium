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

import pytest
from pytest_mock import MockerFixture

from gravel.controllers.gstate import GlobalState


@pytest.mark.asyncio
async def test_state(
    mocker: MockerFixture,
    gstate: GlobalState
):
    from gravel.controllers.nodes.deployment import (
        DeploymentState,
        NodeStageEnum,
        DeploymentErrorEnum
    )
    mocker.patch.object(DeploymentState, "_load_stage")
    mocker.patch.object(DeploymentState, "_save_stage")

    state = DeploymentState(gstate)
    assert state.nostage
    assert not state.bootstrapping
    assert not state.deployed
    assert not state.joining
    assert not state.error
    assert not state.ready
    assert state.stage == NodeStageEnum.NONE
    assert state.can_start()

    state.mark_bootstrap()
    assert state.bootstrapping
    assert not state.nostage
    assert not state.deployed
    assert not state.joining
    assert not state.error
    assert not state.ready
    assert state.stage == NodeStageEnum.BOOTSTRAPPING
    assert not state.can_start()

    state.mark_deployed()
    assert state.deployed
    assert not state.nostage
    assert not state.bootstrapping
    assert not state.joining
    assert not state.error
    assert not state.ready
    assert state.stage == NodeStageEnum.DEPLOYED
    assert state.can_start()

    state.mark_join()
    assert state.joining
    assert not state.nostage
    assert not state.bootstrapping
    assert not state.deployed
    assert not state.error
    assert not state.ready
    assert state.stage == NodeStageEnum.JOINING
    assert not state.can_start()

    state.mark_ready()
    assert state.ready
    assert not state.nostage
    assert not state.bootstrapping
    assert not state.deployed
    assert not state.joining
    assert not state.error
    assert state.stage == NodeStageEnum.READY
    assert state.can_start()

    state.mark_error(
        code=DeploymentErrorEnum.UNKNOWN_ERROR,
        msg="foobar"
    )
    assert state.error
    assert not state.nostage
    assert not state.bootstrapping
    assert not state.deployed
    assert not state.joining
    assert not state.ready
    assert state.stage == NodeStageEnum.ERROR
    assert state.error_what.code == DeploymentErrorEnum.UNKNOWN_ERROR
    assert state.error_what.msg == "foobar"
    assert not state.can_start()
