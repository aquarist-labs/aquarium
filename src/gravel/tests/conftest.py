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

import httpx
import logging
import os
import pytest
import sys

from asgi_lifespan import LifespanManager
from pyfakefs import fake_filesystem  # pyright: reportMissingTypeStubs=false
from pytest_mock import MockerFixture
from types import SimpleNamespace
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    cast,
)
from _pytest.fixtures import SubRequest

from fastapi import FastAPI

from gravel.controllers.gstate import GlobalState
from gravel.controllers.kv import KV


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def mock_ceph_modules(mocker: MockerFixture):
    class MockRadosError(Exception):
        def __init__(self, message: str, errno: Optional[int] = None):
            super(MockRadosError, self).__init__(message)
            self.errno = errno

        def __str__(self):
            msg = super(MockRadosError, self).__str__()
            if self.errno is None:
                return msg
            return "[errno {0}] {1}".format(self.errno, msg)

    sys.modules.update(
        {
            "rados": mocker.MagicMock(
                Error=MockRadosError, OSError=MockRadosError
            ),
        }
    )


def mock_aetcd_modules(mocker: MockerFixture):
    class MockAetcd3Error(Exception):
        def __init__(self, message: str, errno: Optional[int] = None):
            super().__init__(message)
            self.errno = errno

        def __str__(self):
            msg = super().__str__()
            if self.errno is None:
                return msg
            return f"[errno {self.errno}] {msg}"

    sys.modules.update(
        {
            "aetcd3.etcdrpc": mocker.MagicMock(
                Error=MockAetcd3Error, OSError=MockAetcd3Error
            )
        }
    )


@pytest.fixture(params=["default_ceph.conf"])
def ceph_conf_file_fs(request: SubRequest, fs: fake_filesystem.FakeFilesystem):
    """This fixture uses pyfakefs to stub filesystem calls and return
    any files created with the parent `fs` fixture."""
    fs.add_real_file(  # pyright: reportUnknownMemberType=false
        os.path.join(
            DATA_DIR, request.param  # pyright: reportUnknownArgumentType=false
        ),
        target_path="/etc/ceph/ceph.conf",
    )
    yield fs


@pytest.fixture()
def get_data_contents(  # type: ignore
    fs: fake_filesystem.FakeFilesystem,
) -> str:
    def _get_data_contents(dir: str, fn: str):
        # For tests to be able to access any file we need to  add them to the
        # fake filesystem. (If you open any files before the fakefs is set up
        # they will still be accessible, so this is only as a convenience
        # in-case you've order the `fs` before any other fixtures).
        try:
            fs.add_real_file(os.path.join(dir, fn))
        except FileExistsError:
            pass

        with open(os.path.join(dir, fn), "r") as f:
            contents = f.read()
        return contents

    yield _get_data_contents  # type: ignore


def get_data_contents_raw(dir: str, fn: str):
    print(os.path.join(dir, fn))
    with open(os.path.join(dir, fn), "r") as f:
        contents = f.read()
    return contents


class FakeKV(KV):
    def __init__(self):
        self._client = None
        self._is_open = False
        self._is_closing = False

        self._storage: Dict[str, Any] = {}
        self._watchers: Dict[str, Dict[int, Callable[[str, str], None]]] = {}
        self._watch_id_count = 0

    async def ensure_connection(self) -> None:
        """Open k/v store connection"""
        self._is_open = True

    async def close(self) -> None:
        """Close k/v store connection"""
        self._is_closing = True
        self._is_open = False

    async def put(self, key: str, value: str) -> None:
        """Put key/value pair"""
        assert self._is_open
        self._storage[key] = value
        if key in self._watchers:
            for cb in self._watchers[key].values():
                cb(key, value)

    async def get(self, key: str) -> Optional[str]:
        """Get value for provided key"""
        assert self._is_open
        if key not in self._storage:
            return None
        return self._storage[key]

    async def get_prefix(self, key: str) -> List[str]:
        """Get a range of keys with a prefix"""
        assert self._is_open
        values = []
        for k in self._storage.keys():
            if k.startswith(key):
                values.append(self._storage[k])
        return values

    async def rm(self, key: str) -> None:
        """Remove key from store"""
        assert self._is_open
        if key in self._storage:
            del self._storage[key]

    async def lock(self, key: str):  # type: ignore
        """Lock a given key. Requires compliant consumers."""
        assert self._is_open
        raise Exception("TODO")

    async def watch(
        self, key: str, callback: Callable[[str, str], None]
    ) -> int:
        """Watch updates on a given key"""
        if "key" not in self._watchers:
            self._watchers[key] = {}
        watch_id = self._watch_id_count
        self._watch_id_count += 1
        self._watchers[key][watch_id] = callback
        return watch_id

    async def cancel_watch(self, watch_id: int) -> None:
        """Cancel a watch"""
        assert self._client
        for key, values in self._watchers.items():
            if watch_id in values:
                del self._watchers[key][watch_id]


@pytest.fixture()
@pytest.mark.asyncio
async def aquarium_startup(
    get_data_contents: Callable[[str, str], str], mocker: MockerFixture
):
    async def startup(aquarium_app: FastAPI, aquarium_api: FastAPI):
        from gravel.cephadm.cephadm import Cephadm
        from gravel.controllers.nodes.mgr import (
            NodeMgr,
            NodeError,
            NodeInitStage,
        )
        from gravel.controllers.resources.inventory import Inventory
        from gravel.controllers.resources.devices import Devices
        from gravel.controllers.resources.status import Status
        from gravel.controllers.resources.storage import Storage
        from gravel.controllers.services import Services, ServiceModel
        from gravel.controllers.orch.ceph import Ceph, Mgr, Mon
        from gravel.controllers.nodes.deployment import NodeDeployment
        from gravel.controllers.nodes.errors import NodeCantDeployError
        from fastapi.logger import logger as fastapi_logger

        logger: logging.Logger = fastapi_logger

        class FakeNodeDeployment(NodeDeployment):
            async def _prepare_etcd(
                self, hostname: str, address: str, token: str
            ) -> None:
                assert self._state
                if self._state.bootstrapping:
                    raise NodeCantDeployError("node bootstrapping")
                elif not self._state.nostage:
                    raise NodeCantDeployError("node can't be bootstrapped")

                # We don't need to spawn etcd, just allow gstate to init store
                await self._gstate.init_store()

        class FakeNodeMgr(NodeMgr):
            def __init__(self, gstate: GlobalState):
                super().__init__(gstate)
                self._deployment = FakeNodeDeployment(gstate, self._connmgr)

            async def start(self) -> None:
                assert self._state
                logger.debug(f"start > {self._state}")

                if not self.deployment_state.can_start():
                    raise NodeError("unable to start unstartable node")

                assert self._init_stage == NodeInitStage.NONE

                if self.deployment_state.nostage:
                    await self._node_prepare()
                else:
                    assert (
                        self.deployment_state.ready
                        or self.deployment_state.deployed
                    )
                    assert self._state.hostname
                    assert self._state.address
                    # We don't need to spawn etcd, just allow gstate to init store
                    await self.gstate.init_store()

            async def _obtain_images(self) -> bool:
                return True

        class FakeCephadm(Cephadm):
            async def call(
                self,
                cmd: List[str],
                outcb: Optional[Callable[[str], None]] = None,
            ) -> Tuple[str, str, int]:
                # Implement expected calls to cephadm with testable responses
                if cmd[0] == "pull":
                    return "", "", 0
                elif cmd[0] == "gather-facts":
                    return (
                        get_data_contents(DATA_DIR, "gather_facts_real.json"),
                        "",
                        0,
                    )
                elif cmd == ["ceph-volume", "inventory", "--format", "json"]:
                    return (
                        get_data_contents(DATA_DIR, "inventory_real.json"),
                        "",
                        0,
                    )
                else:
                    print(cmd)
                    print(outcb)
                    raise Exception("Tests should not get here")

        class FakeCeph(Ceph):
            def __init__(self, conf_file: str = "/etc/ceph/ceph.conf"):
                self.conf_file = conf_file
                self._is_connected = False

            def connect(self):
                if not self.is_connected():
                    self.cluster = mocker.Mock()
                    self._is_connected = True

        class FakeServices(Services):
            async def _save(self):
                pass

            async def _load(self):
                pass

            def _create_cephfs(self, svc: ServiceModel):
                pass

            def _create_nfs(self, svc: ServiceModel):
                pass

            def _is_ready(self):
                return True

        class FakeStorage(Storage):  # type: ignore
            available = 2000  # type: ignore
            total = 2000  # type: ignore

        gstate: GlobalState = GlobalState()
        gstate._kvstore = FakeKV()  # pyright: reportPrivateUsage=false

        # init node mgr
        nodemgr: NodeMgr = FakeNodeMgr(gstate)

        # Prep cephadm
        cephadm: Cephadm = FakeCephadm()
        gstate.add_cephadm(cephadm)

        # Set up Ceph connections
        ceph: Ceph = FakeCeph()
        ceph_mgr: Mgr = Mgr(ceph)
        gstate.add_ceph_mgr(ceph_mgr)
        ceph_mon: Mon = Mon(ceph)
        gstate.add_ceph_mon(ceph_mon)

        # Set up all of the tickers
        devices: Devices = Devices(
            gstate.config.options.devices.probe_interval,
            nodemgr,
            ceph_mgr,
            ceph_mon,
        )
        gstate.add_devices(devices)

        status: Status = Status(
            gstate.config.options.status.probe_interval, gstate, nodemgr
        )
        gstate.add_status(status)

        inventory: Inventory = Inventory(
            gstate.config.options.inventory.probe_interval, nodemgr, gstate
        )
        gstate.add_inventory(inventory)

        storage: Storage = FakeStorage(
            gstate.config.options.storage.probe_interval, nodemgr, ceph_mon
        )
        gstate.add_storage(storage)

        services: Services = FakeServices(
            gstate.config.options.services.probe_interval, gstate, nodemgr
        )
        gstate.add_services(services)

        await nodemgr.start()
        await gstate.start()

        # Add instances into FastAPI's state:
        aquarium_api.state.gstate = gstate
        aquarium_api.state.nodemgr = nodemgr

    yield startup


@pytest.fixture()
@pytest.mark.asyncio
async def aquarium_shutdown():
    async def shutdown(aquarium_app: FastAPI, aquarium_api: FastAPI):
        print("Shutdown gstate & nodemgr")
        await aquarium_api.state.gstate.shutdown()
        await aquarium_api.state.nodemgr.shutdown()

    yield shutdown


@pytest.fixture
@pytest.mark.asyncio
async def app_state(
    aquarium_startup: Callable[[FastAPI, FastAPI], Awaitable[None]],
    aquarium_shutdown: Callable[[FastAPI, FastAPI], Awaitable[None]],
):
    class FakeFastAPI:
        state = SimpleNamespace()

    aquarium_app = cast(FastAPI, FakeFastAPI())
    aquarium_api = cast(FastAPI, FakeFastAPI())
    await aquarium_startup(aquarium_app, aquarium_api)
    yield aquarium_api.state
    await aquarium_shutdown(aquarium_app, aquarium_api)


@pytest.fixture()
def gstate(app_state: SimpleNamespace):
    yield app_state.gstate


@pytest.fixture
def global_nodemgr(app_state: SimpleNamespace):
    yield app_state.nodemgr


@pytest.fixture()
@pytest.mark.asyncio
async def services(gstate: GlobalState):
    return gstate.services


@pytest.fixture()
def app(caplog: Any, aquarium_startup: FastAPI, aquarium_shutdown: FastAPI):
    caplog.set_level(logging.DEBUG)
    import aquarium

    return aquarium.aquarium_factory(
        startup_method=aquarium_startup, shutdown_method=aquarium_shutdown
    )


@pytest.fixture
async def app_lifespan(app: Any):
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def async_client(app_lifespan: Any):
    async with httpx.AsyncClient(
        app=app_lifespan, base_url="http://aquarium"
    ) as client:
        yield client
