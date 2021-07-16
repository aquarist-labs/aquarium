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

from __future__ import annotations

from json.decoder import JSONDecodeError
from pydantic.tools import parse_obj_as
import json
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Any,
    List,
    Optional,
    Union,
)
from logging import Logger
from fastapi.logger import logger as fastapi_logger
import sys

from gravel.controllers.orch.models import (
    CephDFModel,
    CephOSDDFModel,
    CephOSDMapModel,
    CephOSDPoolEntryModel,
    CephOSDPoolStatsModel,
    CephStatusModel,
)

# Attempt to import rados
# NOTE(jhesketh): rados comes from a system package and cannot be installed from
#                 pypi. So for testing it may not exist on the machine. A check
#                 is made in `Ceph.connect` for whether the package exists.
#                 Tests overwrite this to simulate their own cluster.
try:
    import rados
except ModuleNotFoundError:
    pass


logger: Logger = fastapi_logger

CEPH_CONF_FILE = "/etc/ceph/ceph.conf"


class CephError(Exception):
    def __init__(self, msg: Optional[str] = "", rc: int = 1):
        super().__init__()
        self._msg = msg
        self._rc = rc if rc >= 0 else -rc

    @property
    def message(self) -> str:
        return self._msg if self._msg else "node error"

    @property
    def rc(self) -> int:
        return self._rc

    def __str__(self) -> str:
        return str(self.message)


class CephNotConnectedError(CephError):
    pass


class CephCommandError(CephError):
    pass


class NoRulesetError(CephError):
    pass


class MissingSystemDependency(Exception):
    pass


class Ceph:

    cluster: rados.Rados

    def __init__(self, conf_file: str = CEPH_CONF_FILE):
        self.conf_file = conf_file
        self._is_connected = False

    def _check_config(self):
        path = Path(self.conf_file)
        if not path.exists():
            raise FileNotFoundError(self.conf_file)

    def connect(self):
        self._check_config()

        if "rados" not in sys.modules:
            raise MissingSystemDependency("python3-rados module not found")

        if not self.is_connected():
            self.cluster = rados.Rados(conffile=self.conf_file)
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
                raise CephError(str(e)) from e

            try:
                self.cluster.require_state("connected")
            except rados.RadosStateError as e:
                raise CephError(str(e)) from e

            self._is_connected = True

    def __del__(self):
        if hasattr(self, "cluster") and self.cluster:
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
            raise CephError(str(e))

    def _cmd(
        self,
        func: Callable[[str, bytes], Any],
        cmd: Dict[str, Any],
        inbuf: bytes = b"",
    ) -> Any:
        self.assert_is_ready()
        cmdstr: str = json.dumps(cmd)

        try:
            rc, out, outstr = func(cmdstr, inbuf)
        except Exception as e:
            raise CephCommandError(str(e))

        res: Dict[str, Any] = {}
        if rc != 0:
            logger.error(f"error running command: rc = {rc}, reason = {outstr}")
            raise CephCommandError(outstr, rc=rc)
        if out:
            try:
                res = json.loads(out)
            except JSONDecodeError:  # maybe free-form?
                res = {"result": out}
        elif outstr:  # assume 'outstr' always as free-form text
            res = {"result": outstr}
        return res

    def mon(self, cmd: Dict[str, Any]) -> Any:
        self.connect()
        return self._cmd(self.cluster.mon_command, cmd)

    def mgr(self, cmd: Dict[str, Any], inbuf: bytes = b"") -> Any:
        self.connect()
        return self._cmd(self.cluster.mgr_command, cmd, inbuf)


class Mgr:
    ceph: Ceph

    def __init__(self, ceph: Ceph):
        self.ceph = ceph

    def call(self, cmd: Dict[str, Any], inbuf: bytes = b"") -> Any:
        return self.ceph.mgr(cmd, inbuf=inbuf)


class Mon:
    ceph: Ceph

    def __init__(self, ceph: Ceph):
        self.ceph = ceph

    def call(self, cmd: Dict[str, Any]) -> Any:
        return self.ceph.mon(cmd)

    @property
    def status(self) -> CephStatusModel:
        cmd: Dict[str, Any] = {"prefix": "status", "format": "json"}
        result: Dict[str, Any] = self.call(cmd)  # propagate exception
        return CephStatusModel.parse_obj(result)

    def df(self) -> CephDFModel:
        cmd: Dict[str, str] = {"prefix": "df", "format": "json"}
        result: Dict[str, Any] = self.call(cmd)
        return CephDFModel.parse_obj(result)

    def osd_df(self) -> CephOSDDFModel:
        cmd: Dict[str, str] = {"prefix": "osd df", "format": "json"}
        result: Dict[str, Any] = self.call(cmd)
        return CephOSDDFModel.parse_obj(result)

    def get_osdmap(self) -> CephOSDMapModel:
        cmd: Dict[str, str] = {"prefix": "osd dump", "format": "json"}
        result: Dict[str, Any] = self.call(cmd)
        return CephOSDMapModel.parse_obj(result)

    def get_pools(self) -> List[CephOSDPoolEntryModel]:
        osdmap = self.get_osdmap()
        return osdmap.pools

    def _get_ruleset_id(self, name: str) -> int:
        cmd = {"prefix": "osd crush rule dump", "format": "json"}
        try:
            result = self.call(cmd)
            assert type(result) == list
            rulesetid: Optional[int] = None
            for ruleset in result:
                assert "rule_name" in ruleset
                assert "ruleset" in ruleset
                if ruleset["rule_name"] == name:
                    rulesetid = ruleset["ruleset"]
                    break
            assert rulesetid is not None
            return rulesetid
        except CephCommandError as e:
            logger.error(f"mon > unable to obtain ruleset id: {str(e)}")
            logger.exception(e)
            raise NoRulesetError()

    def config_get(self, who: str, name: str) -> Any:
        cmd = {
            "prefix": "config get",
            "who": who,
            "key": name,
        }
        try:
            value = self.call(cmd)
        except CephCommandError as e:
            logger.error(f"mon > unable to get config: {name} on {who}")
            logger.exception(e)
            return None
        return value

    def config_set(self, who: str, name: str, value: str) -> bool:
        cmd = {"prefix": "config set", "who": who, "name": name, "value": value}
        try:
            self.call(cmd)
        except CephCommandError as e:
            logger.error(
                f"mon > unable to set config: {name} = {value} on {who}"
            )
            logger.exception(e)
            return False
        return True

    def pool_set(
        self, poolname: str, var: str, value: str, really: bool = False
    ) -> bool:
        """Set given pool's configuration variable to a provided value"""
        assert poolname
        assert var
        assert value
        cmd: Dict[str, Union[str, bool]] = {
            "prefix": "osd pool set",
            "pool": poolname,
            "var": var,
            "val": value,
        }
        if really:
            cmd["yes_i_really_mean_it"] = True

        try:
            self.call(cmd)
        except CephCommandError as e:
            logger.error(
                f"mon > unable to set {var} = {value} on pool {poolname}"
            )
            logger.exception(e)
            return False
        return True

    def _set_default_ruleset_config(self, rulesetid: int) -> bool:
        r = self.config_set(
            "global", "osd_pool_default_crush_rule", str(rulesetid)
        )
        if not r:
            logger.error("mon > unable to set default crush rule")
            return False
        return True

    def set_default_ruleset(self) -> bool:
        cmd: Dict[str, str] = {
            "prefix": "osd crush rule create-replicated",
            "name": "single_node_rule",
            "root": "default",
            "type": "osd",
        }
        try:
            self.call(cmd)
        except CephCommandError as e:
            logger.error(
                f"mon > unable to create single-node ruleset: {str(e)}"
            )
            logger.exception(e)
            return False

        rulesetid: int = -1
        try:
            rulesetid = self._get_ruleset_id("single_node_rule")
        except NoRulesetError:
            return False

        if not self._set_default_ruleset_config(rulesetid):
            return False

        return True

    def set_replicated_ruleset(self) -> bool:
        rulesetid = self._get_ruleset_id("replicated_rule")
        assert rulesetid >= 0
        if not self._set_default_ruleset_config(rulesetid):
            return False

        expected_rulesetid = self._get_ruleset_id("single_node_rule")
        assert expected_rulesetid >= 0
        pools: List[CephOSDPoolEntryModel] = self.get_pools()
        for pool in pools:
            if pool.crush_rule != expected_rulesetid:
                # the user must have changed the ruleset, let them keep it.
                logger.info(
                    "skipping setting replicated rule on pool "
                    f"{pool.pool_name} because it has a user-defined rule"
                )
                continue
            if not self.set_pool_ruleset(pool.pool_name, "replicated_rule"):
                return False
        return True

    def set_pool_ruleset(self, poolname: str, ruleset: str) -> bool:
        """Set a given pool's ruleset. Expects a ruleset's name."""
        assert ruleset
        r = self.pool_set(poolname, "crush_rule", ruleset)
        if not r:
            logger.error(f"mon > unable to set pool crush ruleset to {ruleset}")
        return r

    def set_pool_size(self, name: str, size: int) -> None:
        """
        Set a given pool's size to the provided value.
        If the provided value is greater than 2, sets min_size to 2; otherwise
        sets min_size to 1.
        """
        really: bool = False
        if size == 1:
            really = True
        r = self.pool_set(name, "size", str(size), really=really)
        if not r:
            logger.error("mon > unable to set pool size")

        minsize = 2 if size > 2 else 1
        r = self.pool_set(name, "min_size", str(minsize))
        if not r:
            logger.error("mon > unable to set pool min_size")

    def set_allow_pool_size_one(self) -> None:
        r = self.config_set("global", "mon_allow_pool_size_one", "true")
        if not r:
            logger.error("mon > unable to set allow pool size one")

    def disable_warn_on_no_redundancy(self) -> None:
        r = self.config_set("global", "mon_warn_on_pool_no_redundancy", "false")
        if not r:
            logger.error("mon > unable to disable warn on no redundancy")

    def get_pools_stats(self) -> List[CephOSDPoolStatsModel]:
        cmd: Dict[str, str] = {"prefix": "osd pool stats", "format": "json"}
        results: Dict[str, Any] = self.call(cmd)
        return parse_obj_as(List[CephOSDPoolStatsModel], results)

    def get_pool_default_size(self) -> Optional[int]:
        return self.config_get("mon", "osd_pool_default_size")

    def set_pool_default_size(self, size: int) -> bool:
        r = self.config_set("global", "osd_pool_default_size", str(size))
        if not r:
            logger.error("mon > unable to set osd pool default size: {size}")
        return r
