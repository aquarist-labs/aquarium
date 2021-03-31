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
from pydantic.tools import parse_obj_as
import rados
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Any,
    List,
    Optional
)
from logging import Logger
from fastapi.logger import logger as fastapi_logger
from gravel.controllers.orch.models import (
    CephDFModel,
    CephOSDDFModel,
    CephOSDMapModel,
    CephOSDPoolEntryModel, CephOSDPoolStatsModel,
    CephStatusModel
)


logger: Logger = fastapi_logger

CEPH_CONF_FILE = '/etc/ceph/ceph.conf'


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
            raise CephError(str(e)) from e

        try:
            self.cluster.require_state("connected")
        except rados.RadosStateError as e:
            raise CephError(str(e)) from e

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
            raise CephError(str(e))

    def _cmd(self, func: Callable[[str, bytes], Any],
             cmd: Dict[str, Any]
             ) -> Any:
        self.assert_is_ready()
        cmdstr: str = json.dumps(cmd)

        try:
            rc, out, outstr = func(cmdstr, b"")
        except Exception as e:
            raise CephCommandError(str(e))

        res: Dict[str, Any] = {}
        if rc != 0:
            logger.error(
                f"error running command: rc = {rc}, reason = {outstr}")
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

    def osd_df(self) -> CephOSDDFModel:
        cmd: Dict[str, str] = {
            "prefix": "osd df",
            "format": "json"
        }
        result: Dict[str, Any] = self.call(cmd)
        return CephOSDDFModel.parse_obj(result)

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

    def _get_ruleset_id(self, name: str) -> int:
        cmd = {
            "prefix": "osd crush rule dump",
            "format": "json"
        }
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

    def _set_default_ruleset_config(self, rulesetid: int) -> bool:
        cmd = {
            "prefix": "config set",
            "who": "global",
            "name": "osd_pool_default_crush_rule",
            "value": f"{rulesetid}"
        }
        try:
            self.call(cmd)
        except CephCommandError as e:
            logger.error(f"mon > unable to set default crush rule: {str(e)}")
            logger.exception(e)
            return False
        return True

    def set_default_ruleset(self) -> bool:
        cmd: Dict[str, str] = {
            "prefix": "osd crush rule create-replicated",
            "name": "single_node_rule",
            "root": "default",
            "type": "osd"
        }
        try:
            self.call(cmd)
        except CephCommandError as e:
            logger.error(
                f"mon > unable to create single-node ruleset: {str(e)}")
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
        assert ruleset
        cmd: Dict[str, str] = {
            "prefix": "osd pool set",
            "pool": poolname,
            "var": "crush_rule",
            "val": ruleset
        }
        try:
            self.call(cmd)
        except CephCommandError as e:
            logger.error(f"mon > unable to set pool crush ruleset: {str(e)}")
            logger.exception(e)
            return False
        return True

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
            logger.error("mon > unable to set pool size")
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
            logger.error("mon > unable to set pool min_size")
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

    def get_pools_stats(self) -> List[CephOSDPoolStatsModel]:
        cmd: Dict[str, str] = {
            "prefix": "osd pool stats",
            "format": "json"
        }
        results: Dict[str, Any] = self.call(cmd)
        return parse_obj_as(List[CephOSDPoolStatsModel], results)
