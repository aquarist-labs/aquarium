# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

import pytest
from typing import List


@pytest.mark.asyncio
async def test_create(services):
    from gravel.controllers.services import ServiceTypeEnum

    svc = await services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 2)
    assert svc.name == "foobar"
    assert svc.type == ServiceTypeEnum.CEPHFS
    assert svc.reservation == 1000
    assert svc.replicas == 2
    assert "foobar" in services._services  # pyright: reportPrivateUsage=false


@pytest.mark.asyncio
async def test_create_fail_reservation(services):
    from gravel.controllers.services import \
        ServiceTypeEnum, NotEnoughSpaceError
    with pytest.raises(NotEnoughSpaceError):
        await services.create("foobar", ServiceTypeEnum.CEPHFS, 3000, 2)


@pytest.mark.asyncio
async def test_create_exists(services):
    from gravel.controllers.services import \
        ServiceTypeEnum, ServiceExistsError

    await services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 1)
    with pytest.raises(ServiceExistsError):
        await services.create("foobar", ServiceTypeEnum.CEPHFS, 1, 1)


@pytest.mark.asyncio
async def test_create_over_reserved(services):
    from gravel.controllers.services import \
        ServiceTypeEnum, NotEnoughSpaceError

    await services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 2)
    with pytest.raises(NotEnoughSpaceError):
        # TODO(jhesketh): Add in matches for checking the expected numbers
        await services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)


def test_remove():
    # TODO: add missing tests
    pass


@pytest.mark.asyncio
async def test_ls(services):
    from gravel.controllers.services import \
        ServiceModel, ServiceTypeEnum

    await services.create("foobar", ServiceTypeEnum.CEPHFS, 1, 1)
    await services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)

    lst: List[ServiceModel] = services.ls()
    names = [x.name for x in lst]
    assert "foobar" in names
    assert "barbaz" in names


@pytest.mark.asyncio
async def test_reservations(services):
    from gravel.controllers.services import ServiceTypeEnum

    await services.create("foobar", ServiceTypeEnum.CEPHFS, 20, 1)
    await services.create("barbaz", ServiceTypeEnum.CEPHFS, 100, 2)

    assert services.total_reservation == 120
    assert services.total_raw_reservation == 220


@pytest.mark.asyncio
async def test_get(services):
    from gravel.controllers.services import \
        ServiceTypeEnum, UnknownServiceError

    with pytest.raises(UnknownServiceError):
        services.get("foobar")

    await services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)
    services.get("barbaz")


@pytest.mark.asyncio
async def test_check_requirements(services):
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

    await services.create("foobar", ServiceTypeEnum.CEPHFS, 700, 1)
    feasible, req = services.check_requirements(1000, 1)
    assert feasible is True
    assert req.required == 1000
    assert req.available == 1300
    assert req.reserved == 700

    feasible, req = services.check_requirements(1000, 2)
    assert feasible is False
    assert req.required == 2000
    assert req.available == 1300
    assert req.reserved == 700

    await services.create("barbaz", ServiceTypeEnum.CEPHFS, 500, 1)
    feasible, req = services.check_requirements(1000, 1)
    assert feasible is False
    assert req.required == 1000
    assert req.available == 800
    assert req.reserved == 1200
