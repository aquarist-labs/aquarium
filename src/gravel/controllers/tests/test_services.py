# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from typing import Any, List
from unittest import mock, TestCase


def mock_save(cls: Any) -> None:
    pass


def mock_load(cls: Any) -> None:
    pass


def mock_create(cls: Any, svc: Any) -> None:
    pass


class MockStorage(mock.MagicMock):
    available = 2000


with mock.patch('gravel.controllers.config.Config'):
    with mock.patch(
            "gravel.controllers.resources.storage", MockStorage
    ):
        from gravel.controllers.services import \
            Services, ServiceModel, ServiceTypeEnum, \
            NotEnoughSpaceError, ServiceExistsError, \
            UnknownServiceError


@mock.patch.object(Services, "_save", new=mock_save)
@mock.patch.object(Services, "_load", new=mock_load)
@mock.patch.object(Services, "_create_service", new=mock_create)
class TestServices(TestCase):

    def test_create(self):

        services = Services()
        svc = services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 2)
        self.assertEqual(svc.name, "foobar")
        self.assertEqual(svc.type, ServiceTypeEnum.CEPHFS)
        self.assertEqual(svc.reservation, 1000)
        self.assertEqual(svc.replicas, 2)
        self.assertIn(
            "foobar",
            services._services  # pyright: reportPrivateUsage=false
        )
        pass

    def test_create_fail_reservation(self):
        services = Services()
        try:
            services.create("foobar", ServiceTypeEnum.CEPHFS, 3000, 2)
        except NotEnoughSpaceError:
            return True
        self.fail("expected reservation error")

    def test_create_exists(self):
        services = Services()
        services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 1)
        try:
            services.create("foobar", ServiceTypeEnum.CEPHFS, 1, 1)
        except ServiceExistsError:
            return True
        self.fail("expected service to exist")

    def test_create_over_reserved(self):
        services = Services()
        services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 2)
        try:
            services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)
        except NotEnoughSpaceError:
            return True
        self.fail("expected reservation error")

    def test_remove(self):
        pass

    def test_ls(self):
        services = Services()
        services.create("foobar", ServiceTypeEnum.CEPHFS, 1, 1)
        services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)

        lst: List[ServiceModel] = services.ls()
        names = [x.name for x in lst]
        self.assertIn("foobar", names)
        self.assertIn("barbaz", names)

    def test_reservations(self):
        services = Services()
        services.create("foobar", ServiceTypeEnum.CEPHFS, 20, 1)
        services.create("barbaz", ServiceTypeEnum.CEPHFS, 100, 2)

        self.assertEqual(services.total_reservation, 120)
        self.assertEqual(services.total_raw_reservation, 220)

    def test_get(self):
        services = Services()
        try:
            services.get("foobar")
        except UnknownServiceError:
            pass
        else:
            self.fail("expected unknown service")

        services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)
        try:
            services.get("barbaz")
        except UnknownServiceError:
            self.fail("expected service to exist")

    def test_check_requirements(self):
        services = Services()
        feasible, req = services.check_requirements(1000, 1)
        self.assertTrue(feasible)
        self.assertEqual(req.required, 1000)
        self.assertEqual(req.available, 2000)
        self.assertEqual(req.reserved, 0)

        feasible, req = services.check_requirements(1000, 3)
        self.assertFalse(feasible)
        self.assertEqual(req.required, 3000)
        self.assertEqual(req.available, 2000)
        self.assertEqual(req.reserved, 0)

        services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 1)
        feasible, req = services.check_requirements(1000, 1)
        self.assertTrue(feasible)
        self.assertEqual(req.required, 1000)
        self.assertEqual(req.available, 2000)
        self.assertEqual(req.reserved, 1000)

        feasible, req = services.check_requirements(1000, 2)
        self.assertFalse(feasible)
        self.assertEqual(req.required, 2000)
        self.assertEqual(req.available, 2000)
        self.assertEqual(req.reserved, 1000)

        services.create("barbaz", ServiceTypeEnum.CEPHFS, 1000, 1)
        feasible, req = services.check_requirements(1000, 1)
        self.assertFalse(feasible)
        self.assertEqual(req.required, 1000)
        self.assertEqual(req.available, 2000)
        self.assertEqual(req.reserved, 2000)
