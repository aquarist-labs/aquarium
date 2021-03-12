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
from typing import Any, Generator, Optional
import pytest
import sys
from unittest import mock
from pyfakefs import fake_filesystem  # pyright: reportMissingTypeStubs=false
from _pytest.fixtures import SubRequest
from pytest_mock import MockerFixture

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def mock_ceph_modules():
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
        'rados': mock.MagicMock(Error=MockRadosError, OSError=MockRadosError),
    })


mock_ceph_modules()


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
def gstate(mocker: MockerFixture):
    mocker.patch('gravel.controllers.config.Config')
    from gravel.controllers.gstate import gstate as _gstate
    yield _gstate


@pytest.fixture()
def services(gstate: Generator[Any, None, None], mocker: MockerFixture):
    class MockStorage(mocker.MagicMock):  # type: ignore
        available = 2000
    mocker.patch('gravel.controllers.resources.storage', MockStorage)
    mocker.patch('gravel.controllers.services.Services._save')
    mocker.patch('gravel.controllers.services.Services._load')
    mocker.patch('gravel.controllers.services.Services._create_service')
    from gravel.controllers.services import Services
    services = Services()
    yield services
