# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import rados
from pathlib import Path
from typing import Dict, Any


class CephError(Exception):
    pass

class CephNotConnectedError(CephError):
    pass


class Ceph:

    cluster: rados.Rados

    def __init__(self, confpath: str="/etc/ceph/ceph.conf"):

        path = Path(confpath)
        if not path.exists():
            raise FileNotFoundError(confpath)

        self.cluster = rados.Rados(conffile=confpath)
        if not self.cluster:
            raise CephError("error creating cluster handle")

        # apparently we can't rely on argument "timeout" because it's not really
        # supported by the C API, and thus the python bindings simply expose it
        # until some day when it's supposed to be dropped.
        # This is mighty annoying because we can, technically, get stuck here
        # forever.
        try:
            self.cluster.connect()
        except Exception as e:
            raise CephError(e) from e

        try:
            self.cluster.require_state("connected")
        except rados.RadosStateError as e:
            raise CephError(e) from e

        self._is_connected = True

    def __del__(self):
        if self.cluster:
            self.cluster.shutdown()
            self._is_connected = False

    def is_connected(self):
        return self._is_connected

    def assert_is_ready(self):
        if not self.cluster or not self.is_connected():
            raise CephNotConnectedError()

    @property
    def fsid(self):
        self.assert_is_ready()
        try:
            return self.cluster.get_fsid()
        except Exception as e:
            raise CephError(e)

    def call(self, cmd: Dict[str, Any]) -> str:
        # just a stub for now
        return ""


if __name__ == "__main__":
    mgr = Ceph()
    print(f"fsid: {mgr.fsid}")
