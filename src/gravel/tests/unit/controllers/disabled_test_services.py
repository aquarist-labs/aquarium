# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import pytest
from typing import List


def test_create(services):
    from gravel.controllers.services import ServiceTypeEnum

    svc = services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 2)
    assert svc.name == "foobar"
    assert svc.type == ServiceTypeEnum.CEPHFS
    assert svc.reservation == 1000
    assert svc.replicas == 2
    assert "foobar" in services._services  # pyright: reportPrivateUsage=false


def test_create_fail_reservation(services):
    from gravel.controllers.services import \
        ServiceTypeEnum, NotEnoughSpaceError
    with pytest.raises(NotEnoughSpaceError):
        services.create("foobar", ServiceTypeEnum.CEPHFS, 3000, 2)


def test_create_exists(services):
    from gravel.controllers.services import \
        ServiceTypeEnum, ServiceExistsError

    services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 1)
    with pytest.raises(ServiceExistsError):
        services.create("foobar", ServiceTypeEnum.CEPHFS, 1, 1)


def test_create_over_reserved(services):
    from gravel.controllers.services import \
        ServiceTypeEnum, NotEnoughSpaceError

    services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 2)
    with pytest.raises(NotEnoughSpaceError):
        # TODO(jhesketh): Add in matches for checking the expected numbers
        services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)


def test_remove():
    # TODO: add missing tests
    pass


def test_ls(services):
    from gravel.controllers.services import \
        ServiceModel, ServiceTypeEnum

    services.create("foobar", ServiceTypeEnum.CEPHFS, 1, 1)
    services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)

    lst: List[ServiceModel] = services.ls()
    names = [x.name for x in lst]
    assert "foobar" in names
    assert "barbaz" in names


def test_reservations(services):
    from gravel.controllers.services import ServiceTypeEnum

    services.create("foobar", ServiceTypeEnum.CEPHFS, 20, 1)
    services.create("barbaz", ServiceTypeEnum.CEPHFS, 100, 2)

    assert services.total_reservation == 120
    assert services.total_raw_reservation == 220


def test_get(services):
    from gravel.controllers.services import \
        ServiceTypeEnum, UnknownServiceError

    with pytest.raises(UnknownServiceError):
        services.get("foobar")

    services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)
    services.get("barbaz")


def test_check_requirements(services):
    from gravel.controllers.services import ServiceTypeEnum

    feasible, req = services.check_requirements(1000, 1)
    assert feasible is True
    assert req.required == 1000
    assert req.available == 2000
    assert req.reserved == 0

    feasible, req = services.check_requirements(1000, 3)
    assert feasible is False
    assert req.required == 3000
    assert req.available == 2000
    assert req.reserved == 0

    services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 1)
    feasible, req = services.check_requirements(1000, 1)
    assert feasible is True
    assert req.required == 1000
    assert req.available == 2000
    assert req.reserved == 1000

    feasible, req = services.check_requirements(1000, 2)
    assert feasible is False
    assert req.required == 2000
    assert req.available == 2000
    assert req.reserved == 1000

    services.create("barbaz", ServiceTypeEnum.CEPHFS, 1000, 1)
    feasible, req = services.check_requirements(1000, 1)
    assert feasible is False
    assert req.required == 1000
    assert req.available == 2000
    assert req.reserved == 2000
