# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import rados  # type: ignore
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Tuple


class CephError(Exception):
    pass


class CephNotConnectedError(CephError):
    pass


class CephCommandError(CephError):
    pass


class Ceph(ABC):

    cluster: rados.Rados

    def __init__(self, confpath: str = "/etc/ceph/ceph.conf"):

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

    def mon(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        self.assert_is_ready()
        try:
            cmdstr: str = json.dumps(cmd)
            rc, out, outstr = self.cluster.mon_command(cmdstr, b"")
            res: Dict[str, Any] = {}
            if rc != 0:
                raise CephCommandError(outstr)
            if out:
                res = json.loads(out)
            elif outstr:
                res = json.loads(out)
            return res
        except Exception as e:
            raise CephCommandError(e) from e

    def mgr(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        return {}

    @abstractmethod
    def call(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("method 'call' has not been implemented")


class Mgr(Ceph):

    def __init__(self):
        super().__init__()

    def call(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        return self.mgr(cmd)


class Mon(Ceph):

    def __init__(self):
        super().__init__()

    def call(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        return self.mon(cmd)

    @property
    def status(self) -> Dict[str, Any]:
        cmd: Dict[str, Any] = {
            "prefix": "status",
            "format": "json"
        }
        result = self.mon(cmd)  # propagate exception
        return result


if __name__ == "__main__":
    mgr = Mgr()
    print(f"fsid: {mgr.fsid}")
    mon = Mon()
    print(f"fsid: {mon.fsid}")
    print(f"status: {mon.status}")
