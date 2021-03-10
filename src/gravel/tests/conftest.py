import os
import pytest
import sys
from unittest import mock


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def mock_ceph_modules():
    class MockRadosError(Exception):
        def __init__(self, message, errno=None):
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
def ceph_conf_file_fs(request, fs):
    """ This fixture uses pyfakefs to stub filesystem calls and return
    any files created with the parent `fs` fixture. """
    fs.add_real_file(
        os.path.join(DATA_DIR, request.param),
        target_path='/etc/ceph/ceph.conf'
    )
    yield fs


@pytest.fixture()
def get_data_contents(fs):
    # For tests to be able to access any files in the DATA_DIR, we need to
    # add them to the fake filesystem. (If you open any files before the
    # fakefs is set up they will still be accessible, so this is only as a
    # convenience in-case you've order the `fs` before any other fixtures).
    fs.add_real_directory(DATA_DIR)

    def _get_data_contents(fn):
        with open(os.path.join(DATA_DIR, fn), 'r') as f:
            contents = f.read()
        return contents
    yield _get_data_contents


@pytest.fixture()
def gstate(mocker):
    mocker.patch('gravel.controllers.config.Config')
    from gravel.controllers.gstate import gstate as _gstate
    yield _gstate


@pytest.fixture()
def services(gstate, mocker):
    class MockStorage(mocker.MagicMock):  # type: ignore
        available = 2000
    mocker.patch('gravel.controllers.resources.storage', MockStorage)
    mocker.patch('gravel.controllers.services.Services._save')
    mocker.patch('gravel.controllers.services.Services._load')
    mocker.patch('gravel.controllers.services.Services._create_service')
    from gravel.controllers.services import Services
    services = Services()
    yield services
