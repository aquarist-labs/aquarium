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

from pytest_mock import MockerFixture

from gravel.controllers.gstate import GlobalState


def test_remove(mocker: MockerFixture, gstate: GlobalState) -> None:
    from gravel.controllers.orch.cephfs import CephFS
    from gravel.controllers.orch.orchestrator import Orchestrator

    mocker.patch("gravel.controllers.orch.orchestrator.Orchestrator.rm_mds")
    mocker.patch("gravel.controllers.orch.ceph.Mon.call")
    mocker.patch("gravel.controllers.orch.ceph.Mon.pool_rm")

    orch = Orchestrator(gstate.ceph_mgr)
    cephfs = CephFS(gstate.ceph_mgr, gstate.ceph_mon)
    cephfs.remove("service_name")

    orch.rm_mds.assert_called_once_with("service_name")  # type: ignore
    gstate.ceph_mon.call.assert_called_once_with(
        {  # type: ignore
            "prefix": "fs rm",
            "fs_name": "service_name",
            "yes_i_really_mean_it": True,
        }
    )
    gstate.ceph_mon.pool_rm.assert_has_calls(
        [  # type: ignore
            mocker.call("cephfs.service_name.data"),
            mocker.call("cephfs.service_name.meta"),
        ]
    )
