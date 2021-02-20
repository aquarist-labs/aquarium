# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import json
import pytest
import unittest.mock

from typing import Any, Dict
from pyfakefs.fake_filesystem_unittest \
    import TestCase  # pyright: reportMissingTypeStubs=false

from gravel.controllers.orch.ceph import Mgr, Mon
from .outputs import mon_df_raw, mon_osdmap_raw

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

    def call(self, raw_value: str) -> Any:
        return json.loads(raw_value)

    def test_mon_df(self):

        mon = Mon()
        mon.call = unittest.mock.MagicMock(  # type: ignore
            return_value=self.call(mon_df_raw))

        res = mon.df()
        self.assertEqual(res.stats.total_bytes, 0)

    def test_get_osdmap(self):
        mon = Mon()
        mon.call = unittest.mock.MagicMock(  # type: ignore
            return_value=self.call(mon_osdmap_raw)
        )
        res = mon.get_osdmap()
        self.assertEqual(res.epoch, 4)

    def test_get_pools(self):
        mon = Mon()
        mon.call = unittest.mock.MagicMock(  # type: ignore
            return_value=self.call(mon_osdmap_raw)
        )
        res = mon.get_pools()
        self.assertEqual(len(res), 0)

    def test_set_pool_size(self):

        def argscheck(cls: Any, args: Dict[str, Any]) -> Any:
            self.assertIn("prefix", args)
            self.assertIn("pool", args)
            self.assertIn("var", args)
            self.assertIn("val", args)
            self.assertEqual(args["prefix"], "osd pool set")
            self.assertEqual(args["pool"], "foobar")
            self.assertEqual(args["var"], "size")
            self.assertEqual(args["val"], "2")

        with unittest.mock.patch.object(
            Mon, "call", new=argscheck  # type:ignore
        ):
            mon = Mon()
            mon.set_pool_size("foobar", 2)
