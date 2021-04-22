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

import os
from typing import Optional
import pytest
import sys
from pyfakefs import fake_filesystem  # pyright: reportMissingTypeStubs=false
from _pytest.fixtures import SubRequest
from pytest_mock import MockerFixture

from gravel.controllers.gstate import GlobalState

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def mock_ceph_modules(mocker):
    class MockRadosError(Exception):
        def __init__(self, message: str, errno: Optional[int] = None):
            super(MockRadosError, self).__init__(message)
            self.errno = errno

        def __str__(self):
            msg = super(MockRadosError, self).__str__()
            if self.errno is None:
                return msg
            return '[errno {0}] {1}'.format(self.errno, msg)

    sys.modules.update({
        'rados': mocker.MagicMock(Error=MockRadosError, OSError=MockRadosError),
    })


def mock_aetcd_modules(mocker):
    class MockAetcd3Error(Exception):
        def __init__(self, message: str, errno: Optional[int] = None):
            super().__init__(message)
            self.errno = errno

        def __str__(self):
            msg = super().__str__()
            if self.errno is None:
                return msg
            return f"[errno {self.errno}] {msg}"

    sys.modules.update({
        'aetcd3.etcdrpc': mocker.MagicMock(Error=MockAetcd3Error, OSError=MockAetcd3Error)
    })


@pytest.fixture(params=['default_ceph.conf'])
def ceph_conf_file_fs(
    request: SubRequest,
    fs: fake_filesystem.FakeFilesystem
):
    """ This fixture uses pyfakefs to stub filesystem calls and return
    any files created with the parent `fs` fixture. """
    fs.add_real_file(  # pyright: reportUnknownMemberType=false
        os.path.join(
            DATA_DIR,
            request.param  # pyright: reportUnknownArgumentType=false
        ),
        target_path='/etc/ceph/ceph.conf'
    )
    yield fs


@pytest.fixture()
def get_data_contents(fs: fake_filesystem.FakeFilesystem):
    def _get_data_contents(dir: str, fn: str):
        # For tests to be able to access any file we need to  add them to the
        # fake filesystem. (If you open any files before the fakefs is set up
        # they will still be accessible, so this is only as a convenience
        # in-case you've order the `fs` before any other fixtures).
        try:
            fs.add_real_file(os.path.join(dir, fn))
        except FileExistsError:
            pass

        with open(os.path.join(dir, fn), 'r') as f:
            contents = f.read()
        return contents
    yield _get_data_contents


@pytest.fixture()
@pytest.mark.asyncio
async def gstate(fs: fake_filesystem.FakeFilesystem, mocker: MockerFixture):
    mock_ceph_modules(mocker)
    mock_aetcd_modules(mocker)

    from gravel.controllers.nodes.mgr import NodeMgr
    from gravel.controllers.resources.inventory import Inventory
    from gravel.controllers.resources.devices import Devices
    from gravel.controllers.resources.status import Status
    from gravel.controllers.resources.storage import Storage
    from gravel.controllers.services import Services, ServiceModel

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
        available = 2000
        total = 2000

    gstate: GlobalState = GlobalState()

    # init node mgr
    nodemgr: NodeMgr = NodeMgr(gstate)

    devices: Devices = Devices(gstate.config.options.devices.probe_interval, nodemgr)
    gstate.add_devices(devices)

    status: Status = Status(gstate.config.options.status.probe_interval, gstate, nodemgr)
    gstate.add_status(status)

    inventory: Inventory = Inventory(gstate.config.options.inventory.probe_interval)
    gstate.add_inventory(inventory)

    storage: Storage = FakeStorage(gstate.config.options.storage.probe_interval, nodemgr)
    gstate.add_storage(storage)

    services: Services = FakeServices(
        gstate.config.options.services.probe_interval, gstate, nodemgr)
    gstate.add_services(services)

    await nodemgr.start()
    await gstate.start()

    return gstate


@pytest.fixture()
@pytest.mark.asyncio
async def services(gstate: GlobalState):
    return gstate.services
