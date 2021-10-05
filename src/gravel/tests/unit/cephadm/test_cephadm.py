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

import json
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest
from pytest_mock import MockerFixture

from gravel.cephadm.cephadm import Cephadm, CephadmError
from gravel.cephadm.models import HostFactsModel, VolumeDeviceModel
from gravel.controllers.config import ContainersOptionsModel

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.mark.asyncio
async def test_bootstrap(mocker: MockerFixture):
    async def mock_call(cmd: str, cb: Optional[Any]) -> Tuple[str, str, int]:
        return "foo", "bar", 0

    cephadm = Cephadm(ContainersOptionsModel())
    mocker.patch.object(cephadm, "call", side_effect=mock_call)

    out, err, rc = await cephadm.bootstrap("127.0.0.1")
    assert out == "foo"
    assert err == "bar"
    assert rc == 0


@pytest.mark.asyncio
async def test_gather_facts_real(
    mocker: MockerFixture, get_data_contents: Callable[[str, str], str]
):
    async def mock_call(cmd: str) -> Tuple[str, str, int]:
        return get_data_contents(DATA_DIR, "gather_facts_real.json"), "", 0

    cephadm = Cephadm(ContainersOptionsModel())
    mocker.patch.object(cephadm, "call", side_effect=mock_call)

    result: HostFactsModel = await cephadm.gather_facts()
    real: Dict[str, Any] = json.loads(
        get_data_contents(DATA_DIR, "gather_facts_real.json")
    )
    assert result.dict() == real


@pytest.mark.asyncio
async def test_gather_facts_fail_1(mocker: MockerFixture):
    async def mock_call(cmd: str) -> Tuple[str, str, int]:
        return "fail", "", 0

    cephadm = Cephadm(ContainersOptionsModel())
    mocker.patch.object(cephadm, "call", side_effect=mock_call)

    with pytest.raises(CephadmError):
        await cephadm.gather_facts()


@pytest.mark.asyncio
async def test_gather_facts_fail_2(
    mocker: MockerFixture, get_data_contents: Callable[[str, str], str]
):
    async def mock_call(cmd: str) -> Tuple[str, str, int]:
        return get_data_contents(DATA_DIR, "gather_facts_real.json"), "", 1

    cephadm = Cephadm(ContainersOptionsModel())
    mocker.patch.object(cephadm, "call", side_effect=mock_call)

    with pytest.raises(CephadmError):
        await cephadm.gather_facts()


@pytest.mark.asyncio
async def test_volume_inventory(
    mocker: MockerFixture, get_data_contents: Callable[[str, str], str]
):
    async def mock_call(cmd: str) -> Tuple[str, str, int]:
        return get_data_contents(DATA_DIR, "inventory_real.json"), "", 0

    cephadm = Cephadm(ContainersOptionsModel())
    mocker.patch.object(cephadm, "call", side_effect=mock_call)

    result: List[VolumeDeviceModel] = await cephadm.get_volume_inventory()

    for dev in result:
        if dev.sys_api.rotational:
            assert dev.human_readable_type == "hdd"
        else:
            assert dev.human_readable_type == "sdd"


@pytest.mark.asyncio
async def test_volume_inventory_fail(mocker: MockerFixture):
    async def mock_call(cmd: str) -> Tuple[str, str, int]:
        return "fail", "", 0

    cephadm = Cephadm(ContainersOptionsModel())
    mocker.patch.object(cephadm, "call", side_effect=mock_call)

    with pytest.raises(CephadmError):
        await cephadm.get_volume_inventory()
