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

# pyright: reportPrivateUsage=false

from typing import Any, Dict, Tuple
import pytest
from pytest_mock import MockerFixture

from gravel.controllers.gstate import GlobalState


@pytest.mark.asyncio
async def test_postbootstrap_config(
    mocker: MockerFixture,
    gstate: GlobalState
) -> None:

    config_keys: Dict[str, Tuple[str, str]] = {}

    def config_set(cls: Any, who: str, name: str, value: str) -> bool:
        config_keys[name] = (who, value)
        return True

    def expect_key(who: str, name: str, value: str) -> None:
        assert name in config_keys
        scope, val = config_keys[name]
        assert scope == who
        assert val == value

    from gravel.controllers.nodes.mgr import NodeMgr
    from gravel.controllers.orch.ceph import Mon
    mocker.patch.object(NodeMgr, "_init_state")
    mocker.patch.object(Mon, "config_set", new=config_set)
    mocker.patch.object(Mon, "call")
    mocker.patch.object(Mon, "set_default_ruleset")  # ignore default ruleset

    mgr = NodeMgr(gstate)
    await mgr._post_bootstrap_config()

    expect_key("global", "mon_allow_pool_size_one", "true")
    expect_key("global", "mon_warn_on_pool_no_redundancy", "false")
    expect_key("mgr", "mgr/cephadm/manage_etc_ceph_ceph_conf", "true")
    expect_key("global", "auth_allow_insecure_global_id_reclaim", "false")
