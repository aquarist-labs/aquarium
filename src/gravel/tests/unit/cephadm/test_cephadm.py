from typing import Any, Dict, List, Optional, Tuple
import json
import os
import pytest

from gravel.cephadm.cephadm import Cephadm, CephadmError
from gravel.cephadm.models \
    import HostFactsModel, NodeInfoModel, VolumeDeviceModel


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


@pytest.mark.asyncio
async def test_bootstrap(mocker):

    async def mock_call(cmd: str, cb: Optional[Any]) -> Tuple[str, str, int]:
        return "foo", "bar", 0

    cephadm = Cephadm()
    mocker.patch.object(cephadm, 'call', side_effect=mock_call)

    out, err, rc = await cephadm.bootstrap("127.0.0.1")
    assert out == "foo"
    assert err == "bar"
    assert rc == 0


@pytest.mark.asyncio
async def test_gather_facts_real(mocker, get_data_contents):
    async def mock_call(cmd: str) -> Tuple[str, str, int]:
        return get_data_contents(DATA_DIR, 'gather_facts_real.json'), "", 0

    cephadm = Cephadm()
    mocker.patch.object(cephadm, 'call', side_effect=mock_call)

    result: HostFactsModel = await cephadm.gather_facts()
    real: Dict[str, Any] = json.loads(
        get_data_contents(DATA_DIR, 'gather_facts_real.json'))
    assert result.dict() == real


@pytest.mark.asyncio
async def test_gather_facts_fail_1(mocker):
    async def mock_call(cmd: str) -> Tuple[str, str, int]:
        return "fail", "", 0

    cephadm = Cephadm()
    mocker.patch.object(cephadm, 'call', side_effect=mock_call)

    with pytest.raises(CephadmError):
        await cephadm.gather_facts()


@pytest.mark.asyncio
async def test_gather_facts_fail_2(mocker, get_data_contents):
    async def mock_call(cmd: str) -> Tuple[str, str, int]:
        return get_data_contents(DATA_DIR, 'gather_facts_real.json'), "", 1

    cephadm = Cephadm()
    mocker.patch.object(cephadm, 'call', side_effect=mock_call)

    with pytest.raises(CephadmError):
        await cephadm.gather_facts()


@pytest.mark.asyncio
async def test_volume_inventory(mocker, get_data_contents):
    async def mock_call(cmd: str) -> Tuple[str, str, int]:
        return get_data_contents(DATA_DIR, 'inventory_real.json'), "", 0

    cephadm = Cephadm()
    mocker.patch.object(cephadm, 'call', side_effect=mock_call)

    result: List[VolumeDeviceModel] = \
        await cephadm.get_volume_inventory()

    for dev in result:
        if dev.sys_api.rotational:
            assert dev.human_readable_type == "hdd"
        else:
            assert dev.human_readable_type == "sdd"


@pytest.mark.asyncio
async def test_volume_inventory_fail(mocker):
    async def mock_call(cmd: str) -> Tuple[str, str, int]:
        return "fail", "", 0

    cephadm = Cephadm()
    mocker.patch.object(cephadm, 'call', side_effect=mock_call)

    with pytest.raises(CephadmError):
        await cephadm.get_volume_inventory()


@pytest.mark.asyncio
async def test_get_node_info(mocker, get_data_contents):
    async def mock_facts_call(cmd: str) -> Tuple[str, str, int]:
        return get_data_contents(DATA_DIR, 'gather_facts_real.json'), "", 0

    async def mock_inventory_call(cmd: str) -> Tuple[str, str, int]:
        return get_data_contents(DATA_DIR, 'inventory_real.json'), "", 0

    cephadm_facts = Cephadm()
    mocker.patch.object(
        cephadm_facts, 'call',
        side_effect=mock_facts_call)
    cephadm_inventory = Cephadm()
    mocker.patch.object(
        cephadm_inventory, 'call',
        side_effect=mock_inventory_call)

    facts_result = await cephadm_facts.gather_facts()
    inventory_result = await cephadm_inventory.get_volume_inventory()

    async def mock_facts_result() -> HostFactsModel:
        return facts_result

    async def mock_inventory_result() -> List[VolumeDeviceModel]:
        return inventory_result

    cephadm = Cephadm()
    mocker.patch.object(
        cephadm, 'gather_facts',
        side_effect=mock_facts_result)
    mocker.patch.object(
        cephadm, 'get_volume_inventory',
        side_effect=mock_inventory_result)

    info: NodeInfoModel = await cephadm.get_node_info()
    assert info.hostname == facts_result.hostname
    assert info.disks == inventory_result
