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

from json.decoder import JSONDecodeError
import rados
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Any,
    List
)
from logging import Logger
from fastapi.logger import logger as fastapi_logger
from gravel.controllers.orch.models import (
    CephDFModel,
    CephOSDMapModel,
    CephOSDPoolEntryModel,
    CephStatusModel
)


logger: Logger = fastapi_logger

CEPH_CONF_FILE = '/etc/ceph/ceph.conf'


class CephError(Exception):
    pass


class CephNotConnectedError(CephError):
    pass


class CephCommandError(CephError):
    pass


class Ceph(ABC):

    cluster: rados.Rados

    def __init__(self, conf_file: str = CEPH_CONF_FILE):

        path = Path(conf_file)
        if not path.exists():
            raise FileNotFoundError(conf_file)

        self.cluster = rados.Rados(conffile=conf_file)
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
        if hasattr(self, 'cluster') and self.cluster:
            self.cluster.shutdown()
            self._is_connected = False

    def is_connected(self):
        return self._is_connected

    def assert_is_ready(self):
        if not self.cluster or not self.is_connected():
            raise CephNotConnectedError()

    @property
    def fsid(self) -> str:
        self.assert_is_ready()
        try:
            return self.cluster.get_fsid()
        except Exception as e:
            raise CephError(e)

    def _cmd(self, func: Callable[[str, bytes], Any],
             cmd: Dict[str, Any]
             ) -> Any:
        self.assert_is_ready()
        try:
            cmdstr: str = json.dumps(cmd)
            rc, out, outstr = func(cmdstr, b"")
            res: Dict[str, Any] = {}
            if rc != 0:
                raise CephCommandError(outstr)
            if out:
                try:
                    res = json.loads(out)
                except JSONDecodeError:  # maybe free-form?
                    res = {"result": out}
            elif outstr:  # assume 'outstr' always as free-form text
                res = {"result": outstr}
            return res
        except Exception as e:
            raise CephCommandError(e) from e

    def mon(self, cmd: Dict[str, Any]) -> Any:
        return self._cmd(self.cluster.mon_command, cmd)

    def mgr(self, cmd: Dict[str, Any]) -> Any:
        return self._cmd(self.cluster.mgr_command, cmd)

    @abstractmethod
    def call(self, cmd: Dict[str, Any]) -> Any:
        raise NotImplementedError("method 'call' has not been implemented")


class Mgr(Ceph):

    def __init__(self, conf_file: str = CEPH_CONF_FILE):
        super().__init__(conf_file=conf_file)

    def call(self, cmd: Dict[str, Any]) -> Any:
        return self.mgr(cmd)


class Mon(Ceph):

    def __init__(self, conf_file: str = CEPH_CONF_FILE):
        super().__init__(conf_file=conf_file)

    def call(self, cmd: Dict[str, Any]) -> Any:
        return self.mon(cmd)

    @property
    def status(self) -> CephStatusModel:
        cmd: Dict[str, Any] = {
            "prefix": "status",
            "format": "json"
        }
        result: Dict[str, Any] = self.call(cmd)  # propagate exception
        return CephStatusModel.parse_obj(result)

    def df(self) -> CephDFModel:
        cmd: Dict[str, str] = {
            "prefix": "df",
            "format": "json"
        }
        result: Dict[str, Any] = self.call(cmd)
        return CephDFModel.parse_obj(result)

    def get_osdmap(self) -> CephOSDMapModel:
        cmd: Dict[str, str] = {
            "prefix": "osd dump",
            "format": "json"
        }
        result: Dict[str, Any] = self.call(cmd)
        return CephOSDMapModel.parse_obj(result)

    def get_pools(self) -> List[CephOSDPoolEntryModel]:
        osdmap = self.get_osdmap()
        return osdmap.pools

    def set_pool_size(self, name: str, size: int) -> None:
        size_cmd: Dict[str, Any] = {
            "prefix": "osd pool set",
            "pool": name,
            "var": "size",
            "val": str(size)
        }
        if size == 1:
            size_cmd["yes_i_really_mean_it"] = True
        try:
            self.call(size_cmd)
        except CephCommandError as e:
            logger.error("=> ceph -- mon > unable to set pool size")
            logger.debug(str(e))
            logger.debug(str(size_cmd))

        minsize = 2 if size > 2 else 1
        minsize_cmd: Dict[str, str] = {
            "prefix": "osd pool set",
            "pool": name,
            "var": "min_size",
            "val": str(minsize)
        }
        try:
            self.call(minsize_cmd)
        except CephCommandError as e:
            logger.error("=> ceph -- mon > unable to set pool min_size")
            logger.debug(str(e))

    def set_allow_pool_size_one(self) -> None:
        cmd: Dict[str, str] = {
            "prefix": "config set",
            "who": "global",
            "name": "mon_allow_pool_size_one",
            "value": "true"
        }
        self.call(cmd)

    def disable_warn_on_no_redundancy(self) -> None:
        cmd: Dict[str, str] = {
            "prefix": "config set",
            "who": "global",
            "name": "mon_warn_on_pool_no_redundancy",
            "value": "false"
        }
        self.call(cmd)
