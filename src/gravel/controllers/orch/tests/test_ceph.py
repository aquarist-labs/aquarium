import pytest
from pyfakefs.fake_filesystem_unittest import TestCase

from gravel.controllers.orch.ceph import Mgr, Mon


class TestCeph(TestCase):

    def setUp(self):
        self.setUpPyfakefs()

    def test_ceph_conf(self):
        conf_file = "ceph.conf"
        with pytest.raises(FileNotFoundError, match=conf_file):
            Mgr(conf_file=conf_file)
            Mon(conf_file=conf_file)
