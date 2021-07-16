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

# pyright: reportUnknownMemberType=false

import json
import os
from typing import Callable, List
from pydantic import parse_obj_as
from pytest_mock import MockerFixture

from gravel.controllers.gstate import GlobalState
from gravel.controllers.orch.models import OrchDevicesPerHostModel
from gravel.controllers.orch.orchestrator import Orchestrator


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def test_device_ls(
    get_data_contents: Callable[[str, str], str],
    mocker: MockerFixture,
    gstate: GlobalState,
) -> None:

    orch = Orchestrator(gstate.ceph_mgr)
    orch.call = mocker.MagicMock(
        return_value=json.loads(
            get_data_contents(DATA_DIR, "device_ls_not_available.json")
        )
    )
    res: List[OrchDevicesPerHostModel] = orch.devices_ls()
    assert res[0].name == "asd"


def test_devices_assimilated(
    get_data_contents: Callable[[str, str], str],
    mocker: MockerFixture,
    gstate: GlobalState,
) -> None:
    def device_ls_gen():
        raw = json.loads(
            get_data_contents(DATA_DIR, "device_ls_not_available.json")
        )
        devicels = parse_obj_as(List[OrchDevicesPerHostModel], raw)
        yield devicels
        devicels[0].devices[1].available = True
        yield devicels

    from gravel.controllers.orch.orchestrator import Orchestrator

    orch = Orchestrator(gstate.ceph_mgr)

    devicegen = device_ls_gen()
    orch.devices_ls = mocker.MagicMock(return_value=next(devicegen))
    assert orch.devices_assimilated("asd", ["/dev/vdb", "/dev/vdc"])

    orch.devices_ls = mocker.MagicMock(return_value=next(devicegen))
    assert not orch.devices_assimilated("asd", ["/dev/vdc"])
