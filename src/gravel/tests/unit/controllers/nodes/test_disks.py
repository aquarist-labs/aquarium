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
# pyright: reportUnknownVariableType=false

import os
from typing import Callable

from pytest_mock import MockerFixture

from gravel.controllers.gstate import GlobalState

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def test_solution(
    mocker: MockerFixture,
    get_data_contents: Callable[[str, str], str],
    gstate: GlobalState,
) -> None:

    from gravel.controllers.inventory.nodeinfo import NodeInfoModel
    from gravel.controllers.nodes.disks import Disks, DiskSolution

    fake_inventory: NodeInfoModel = NodeInfoModel.parse_raw(
        get_data_contents(DATA_DIR, "disks_local_nodeinfo.json")
    )
    gstate.inventory._latest = fake_inventory

    solution: DiskSolution = Disks.gen_solution(gstate)
    assert solution.possible
    assert solution.systemdisk is not None
    assert len(solution.rejected) == 1
    assert len(solution.storage) == 3
    assert solution.systemdisk.path == "/dev/vdb"


def test_solution_with_ssd(
    mocker: MockerFixture,
    get_data_contents: Callable[[str, str], str],
    gstate: GlobalState,
) -> None:
    from gravel.controllers.inventory.nodeinfo import NodeInfoModel
    from gravel.controllers.nodes.disks import Disks, DiskSolution

    fake_inventory: NodeInfoModel = NodeInfoModel.parse_raw(
        get_data_contents(DATA_DIR, "disks_local_nodeinfo_with_ssd.json")
    )
    gstate.inventory._latest = fake_inventory

    solution: DiskSolution = Disks.gen_solution(gstate)
    assert solution.possible
    assert solution.systemdisk is not None
    assert len(solution.rejected) == 1
    assert len(solution.storage) == 3
    assert solution.systemdisk.path == "/dev/vda"
