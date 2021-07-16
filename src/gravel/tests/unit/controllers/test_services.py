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

# pyright: reportPrivateUsage=false

import pytest
from typing import List

from pytest_mock import MockerFixture

from gravel.controllers.gstate import GlobalState
from gravel.controllers.services import Services


@pytest.mark.asyncio
async def test_create(services: Services, gstate: GlobalState):
    from gravel.controllers.services import ServiceTypeEnum

    # we need to ensure we have enough storage to test this
    gstate.storage.available = 4000  # type: ignore
    gstate.storage.total = 4000  # type: ignore

    svc = await services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 2)
    assert svc.name == "foobar"
    assert svc.type == ServiceTypeEnum.CEPHFS
    assert svc.allocation == 1000
    assert svc.replicas == 2
    assert "foobar" in services._services

    svc = await services.create("barbaz", ServiceTypeEnum.NFS, 2000, 1)
    assert svc.name == "barbaz"
    assert svc.type == ServiceTypeEnum.NFS
    assert svc.allocation == 2000
    assert svc.replicas == 1
    assert "barbaz" in services._services


@pytest.mark.asyncio
async def test_create_fail_allocation(services: Services):
    from gravel.controllers.services import ServiceTypeEnum, NotEnoughSpaceError

    with pytest.raises(NotEnoughSpaceError):
        await services.create("foobar", ServiceTypeEnum.CEPHFS, 3000, 2)


@pytest.mark.asyncio
async def test_create_exists(services: Services):
    from gravel.controllers.services import ServiceTypeEnum, ServiceExistsError

    await services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 1)
    with pytest.raises(ServiceExistsError):
        await services.create("foobar", ServiceTypeEnum.CEPHFS, 1, 1)


@pytest.mark.asyncio
async def test_create_over_allocated(services: Services):
    from gravel.controllers.services import ServiceTypeEnum, NotEnoughSpaceError

    await services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 2)
    with pytest.raises(NotEnoughSpaceError):
        # TODO(jhesketh): Add in matches for checking the expected numbers
        await services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)


@pytest.mark.asyncio
async def test_create_not_ready(
    mocker: MockerFixture, services: Services
) -> None:
    from gravel.controllers.services import ServiceTypeEnum, NotReadyError

    services._is_ready = mocker.MagicMock(return_value=False)  # type: ignore
    try:
        await services.create("foobar", ServiceTypeEnum.CEPHFS, 1000, 1)
    except NotReadyError:
        pass


def test_remove(mocker: MockerFixture, services: Services) -> None:
    from gravel.controllers.services import NotReadyError

    services.remove("foo")

    services._is_ready = mocker.MagicMock(return_value=False)  # type: ignore
    try:
        services.remove("bar")
    except NotReadyError:
        pass


@pytest.mark.asyncio
async def test_ls(services: Services):
    from gravel.controllers.services import ServiceModel, ServiceTypeEnum

    await services.create("foobar", ServiceTypeEnum.CEPHFS, 1, 1)
    await services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)

    lst: List[ServiceModel] = services.ls()
    names = [x.name for x in lst]
    assert "foobar" in names
    assert "barbaz" in names


@pytest.mark.asyncio
async def test_allocations(services: Services):
    from gravel.controllers.services import ServiceTypeEnum

    await services.create("foobar", ServiceTypeEnum.CEPHFS, 20, 1)
    await services.create("barbaz", ServiceTypeEnum.CEPHFS, 100, 2)

    assert services.total_allocation == 120
    assert services.total_raw_allocation == 220


@pytest.mark.asyncio
async def test_get(services: Services):
    from gravel.controllers.services import ServiceTypeEnum, UnknownServiceError

    with pytest.raises(UnknownServiceError):
        services.get("foobar")

    await services.create("barbaz", ServiceTypeEnum.CEPHFS, 1, 1)
    services.get("barbaz")


def test_constraints(gstate: GlobalState, services: Services) -> None:

    from gravel.controllers.services import ConstraintsModel

    gstate.storage.available = 2000  # type: ignore
    gstate.storage.total = 2000  # type: ignore

    constraints: ConstraintsModel = services.constraints
    assert constraints.allocations.allocated == 0
    assert constraints.allocations.available == 2000

    # FIXME: we're not testing redundancy or availability constraints because
    # that requires mocking the Devices class.


@pytest.mark.asyncio
async def test_check_requirements(services: Services):
    from gravel.controllers.services import ServiceTypeEnum

    feasible, req = services.check_requirements(1000, 1)
    assert feasible is True
    assert req.required == 1000
    assert req.available == 2000
    assert req.allocated == 0

    feasible, req = services.check_requirements(1000, 3)
    assert feasible is False
    assert req.required == 3000
    assert req.available == 2000
    assert req.allocated == 0

    await services.create("foobar", ServiceTypeEnum.CEPHFS, 700, 1)
    feasible, req = services.check_requirements(1000, 1)
    assert feasible is True
    assert req.required == 1000
    assert req.available == 1300
    assert req.allocated == 700

    feasible, req = services.check_requirements(1000, 2)
    assert feasible is False
    assert req.required == 2000
    assert req.available == 1300
    assert req.allocated == 700

    await services.create("barbaz", ServiceTypeEnum.CEPHFS, 500, 1)
    feasible, req = services.check_requirements(1000, 1)
    assert feasible is False
    assert req.required == 1000
    assert req.available == 800
    assert req.allocated == 1200
