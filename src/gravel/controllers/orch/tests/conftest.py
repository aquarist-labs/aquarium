import sys
from unittest import mock


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
