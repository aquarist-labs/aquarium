import pytest
from pyfakefs.fake_filesystem_unittest import TestCase

from gravel.controllers.orch.ceph import Mgr, Mon

CEPH_CONF_FILE = '/etc/ceph/ceph.conf'
CEPH_CONF_CONTENT = '''
# minimal ceph.conf for 049e7b49-0c86-4373-85a4-cb9d50c374a7
[global]
        fsid = 049e7b49-0c86-4373-85a4-cb9d50c374a7
        mon_host = [v2:192.168.1.1:40919/0,v1:192.168.1.1:40920/0] [v2:192.168.1.1:40921/0,v1:192.168.1.1:40922/0] [v2:192.168.1.1:40923/0,v1:192.168.1.1:40924/0]
'''  # noqa:E501


class TestCeph(TestCase):

    def setUp(self):
        self.setUpPyfakefs()
        self.fs.create_file(CEPH_CONF_FILE, contents=CEPH_CONF_CONTENT)

    def test_ceph_conf(self):
        # default location
        Mgr()
        Mon()

        # custom location
        conf_file = '/foo/bar/baz.conf'
        self.fs.create_file(conf_file, contents=CEPH_CONF_CONTENT)
        Mgr(conf_file=conf_file)
        Mon(conf_file=conf_file)

        # invalid location
        conf_file = "missing.conf"
        with pytest.raises(FileNotFoundError, match=conf_file):
            Mgr(conf_file=conf_file)
            Mon(conf_file=conf_file)
