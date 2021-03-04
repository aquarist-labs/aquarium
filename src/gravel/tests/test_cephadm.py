
from typing import Any, Dict, List, Tuple
import json
import pytest

from gravel.cephadm.cephadm import Cephadm, CephadmError
from gravel.cephadm.models \
    import HostFactsModel, NodeInfoModel, VolumeDeviceModel


@pytest.mark.asyncio
async def test_bootstrap(mocker):

    async def mock_call() -> Tuple[str, str, int]:
        return "foo", "bar", 0

    cephadm = Cephadm()
    cephadm.call = mocker.MagicMock(return_value=mock_call())

    out, err, rc = await cephadm.bootstrap("127.0.0.1")
    assert out == "foo"
    assert err == "bar"
    assert rc == 0


@pytest.mark.asyncio
async def test_gather_facts_real(mocker, get_data_contents):
    async def mock_call() -> Tuple[str, str, int]:
        return get_data_contents('gather_facts_real.json'), "", 0

    cephadm = Cephadm()
    cephadm.call = mocker.MagicMock(return_value=mock_call())

    result: HostFactsModel = await cephadm.gather_facts()
    real: Dict[str, Any] = json.loads(
        get_data_contents('gather_facts_real.json'))
    assert result.dict() == real


@pytest.mark.asyncio
async def test_gather_facts_fail_1(mocker):
    async def mock_call() -> Tuple[str, str, int]:
        return "fail", "", 0

    cephadm = Cephadm()
    cephadm.call = mocker.MagicMock(return_value=mock_call())

    with pytest.raises(CephadmError):
        await cephadm.gather_facts()


@pytest.mark.asyncio
async def test_gather_facts_fail_2(mocker, get_data_contents):
    async def mock_call() -> Tuple[str, str, int]:
        return get_data_contents('gather_facts_real.json'), "", 1

    cephadm = Cephadm()
    cephadm.call = mocker.MagicMock(return_value=mock_call())

    with pytest.raises(CephadmError):
        await cephadm.gather_facts()


@pytest.mark.asyncio
async def test_volume_inventory(mocker, get_data_contents):
    async def mock_call() -> Tuple[str, str, int]:
        return get_data_contents('inventory_real.json'), "", 0

    cephadm = Cephadm()
    cephadm.call = mocker.MagicMock(return_value=mock_call())

    result: List[VolumeDeviceModel] = \
        await cephadm.get_volume_inventory()

    for dev in result:
        if dev.sys_api.rotational:
            assert dev.human_readable_type == "hdd"
        else:
            assert dev.human_readable_type == "sdd"


@pytest.mark.asyncio
async def test_volume_inventory_fail(mocker):
    async def mock_call() -> Tuple[str, str, int]:
        return "fail", "", 0

    cephadm = Cephadm()
    cephadm.call = mocker.MagicMock(return_value=mock_call())

    with pytest.raises(CephadmError):
        await cephadm.get_volume_inventory()


@pytest.mark.asyncio
async def test_get_node_info(mocker, get_data_contents):
    async def mock_facts_call() -> Tuple[str, str, int]:
        return get_data_contents('gather_facts_real.json'), "", 0

    async def mock_inventory_call() -> Tuple[str, str, int]:
        return get_data_contents('inventory_real.json'), "", 0

    cephadm_facts = Cephadm()
    cephadm_facts.call = mocker.MagicMock(
        return_value=mock_facts_call())
    cephadm_inventory = Cephadm()
    cephadm_inventory.call = mocker.MagicMock(
        return_value=mock_inventory_call())

    facts_result = await cephadm_facts.gather_facts()
    inventory_result = await cephadm_inventory.get_volume_inventory()

    async def mock_facts_result() -> HostFactsModel:
        return facts_result

    async def mock_inventory_result() -> List[VolumeDeviceModel]:
        return inventory_result

    cephadm = Cephadm()
    cephadm.gather_facts = mocker.MagicMock(
        return_value=mock_facts_result())
    cephadm.get_volume_inventory = mocker.MagicMock(
        return_value=mock_inventory_result())

    info: NodeInfoModel = await cephadm.get_node_info()
    assert info.hostname == facts_result.hostname
    assert info.disks == inventory_result
