
from typing import Any, Dict, List, Tuple
import unittest
import unittest.mock
import json
import pytest

from gravel.cephadm.cephadm import Cephadm, CephadmError
from gravel.cephadm.models \
    import HostFactsModel, NodeInfoModel, VolumeDeviceModel
from gravel.cephadm.tests.outputs import gather_facts_real, inventory_real


class TestCephadm(unittest.IsolatedAsyncioTestCase):

    async def test_bootstrap(self):

        async def mock_call() -> Tuple[str, str, int]:
            return "foo", "bar", 0

        cephadm = Cephadm()
        cephadm.call = unittest.mock.MagicMock(return_value=mock_call())

        out, err, rc = await cephadm.bootstrap("127.0.0.1")
        self.assertEqual(out, "foo")
        self.assertEqual(err, "bar")
        self.assertEqual(rc, 0)

    async def test_gather_facts_real(self):

        async def mock_call() -> Tuple[str, str, int]:
            return gather_facts_real, "", 0

        cephadm = Cephadm()
        cephadm.call = unittest.mock.MagicMock(return_value=mock_call())

        result: HostFactsModel = await cephadm.gather_facts()
        real: Dict[str, Any] = json.loads(gather_facts_real)
        assert result.dict() == real

    async def test_gather_facts_fail_1(self):

        async def mock_call() -> Tuple[str, str, int]:
            return "fail", "", 0

        cephadm = Cephadm()
        cephadm.call = unittest.mock.MagicMock(return_value=mock_call())

        with pytest.raises(CephadmError):
            await cephadm.gather_facts()

    async def test_gather_facts_fail_2(self):

        async def mock_call() -> Tuple[str, str, int]:
            return gather_facts_real, "", 1

        cephadm = Cephadm()
        cephadm.call = unittest.mock.MagicMock(return_value=mock_call())

        with pytest.raises(CephadmError):
            await cephadm.gather_facts()

    async def test_volume_inventory(self):

        async def mock_call() -> Tuple[str, str, int]:
            return inventory_real, "", 0

        cephadm = Cephadm()
        cephadm.call = unittest.mock.MagicMock(return_value=mock_call())

        try:
            result: List[VolumeDeviceModel] = \
                await cephadm.get_volume_inventory()

            for dev in result:
                if dev.sys_api.rotational:
                    self.assertEqual(dev.human_readable_type, "hdd")
                else:
                    self.assertEqual(dev.human_readable_type, "sdd")

        except CephadmError:
            self.fail("unexpected exception")

    async def test_volume_inventory_fail(self):

        async def mock_call() -> Tuple[str, str, int]:
            return "fail", "", 0

        cephadm = Cephadm()
        cephadm.call = unittest.mock.MagicMock(return_value=mock_call())

        with pytest.raises(CephadmError):
            await cephadm.get_volume_inventory()

    async def test_get_node_info(self):

        async def mock_facts_call() -> Tuple[str, str, int]:
            return gather_facts_real, "", 0

        async def mock_inventory_call() -> Tuple[str, str, int]:
            return inventory_real, "", 0

        cephadm_facts = Cephadm()
        cephadm_facts.call = unittest.mock.MagicMock(
            return_value=mock_facts_call())
        cephadm_inventory = Cephadm()
        cephadm_inventory.call = unittest.mock.MagicMock(
            return_value=mock_inventory_call())

        facts_result = await cephadm_facts.gather_facts()
        inventory_result = await cephadm_inventory.get_volume_inventory()

        async def mock_facts_result() -> HostFactsModel:
            return facts_result

        async def mock_inventory_result() -> List[VolumeDeviceModel]:
            return inventory_result

        cephadm = Cephadm()
        cephadm.gather_facts = unittest.mock.MagicMock(
            return_value=mock_facts_result())
        cephadm.get_volume_inventory = unittest.mock.MagicMock(
            return_value=mock_inventory_result())

        info: NodeInfoModel = await cephadm.get_node_info()
        self.assertEqual(info.hostname, facts_result.hostname)
        self.assertEqual(info.disks, inventory_result)
