import pytest
from pyfakefs.fake_filesystem_unittest import TestCase

from gravel.controllers.orch.ceph import Mgr, Mon


class TestCeph(TestCase):

    def setUp(self):
        self.setUpPyfakefs()

    def test_ceph_conf(self):
        with pytest.raises(FileNotFoundError, match="ceph.conf"):
            Mgr()
            Mon()
