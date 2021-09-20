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

import json

import pytest
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_simple_app_response(async_client, mocker: MockerFixture):
    class FakeMemory:
        def __init__(self, total: int):
            self.total = total

    class FakeDisk:
        def __init__(self, total: int):
            self.total = total

    mocker.patch("psutil.cpu_count", return_value=8)
    mocker.patch(
        "psutil.virtual_memory", return_value=FakeMemory(total=33498816512)
    )
    mocker.patch("psutil.disk_usage", return_value=FakeDisk(total=20000000000))

    response = await async_client.get("/api/local/status")
    assert response.status_code == 200
    assert (
        '{"localhost_qualified":{"qualified":true,"errors":[]},"inited":false,"node_stage":0}'
        == response.text
    )
    import asyncio

    await asyncio.sleep(5)

    response = await async_client.get("/api/local/status")
    assert response.status_code == 200
    assert (
        '{"localhost_qualified":{"qualified":true,"errors":[]},"inited":true,"node_stage":0}'
        == response.text
    )


@pytest.mark.asyncio
async def test_localhost_qualified_response(
    async_client, mocker: MockerFixture
):
    class FakeMemory:
        def __init__(self, total: int):
            self.total = total

    class FakeDisk:
        def __init__(self, total: int):
            self.total = total

    # Everything passes
    mocker.patch("psutil.cpu_count", return_value=8)
    mocker.patch(
        "psutil.virtual_memory", return_value=FakeMemory(total=33498816512)
    )
    mocker.patch("psutil.disk_usage", return_value=FakeDisk(total=20000000000))

    response = await async_client.get("/api/local/status")
    assert response.status_code == 200
    response_json = json.loads(response.text)
    assert response_json["localhost_qualified"]["qualified"] is True
    assert response_json["localhost_qualified"]["errors"] == []

    # Failed CPU count
    mocker.patch("psutil.cpu_count", return_value=1)
    mocker.patch(
        "psutil.virtual_memory", return_value=FakeMemory(total=33498816512)
    )
    mocker.patch("psutil.disk_usage", return_value=FakeDisk(total=20000000000))

    response = await async_client.get("/api/local/status")
    assert response.status_code == 200
    response_json = json.loads(response.text)
    assert response_json["localhost_qualified"]["qualified"] is False
    assert response_json["localhost_qualified"]["errors"] == [
        "The node does not have a sufficient number of CPU cores. Required: 2, Actual: 1."
    ]

    # Everything fails
    mocker.patch("psutil.cpu_count", return_value=1)
    mocker.patch(
        "psutil.virtual_memory", return_value=FakeMemory(total=1073741824)
    )
    mocker.patch("psutil.disk_usage", return_value=FakeDisk(total=1073741824))

    response = await async_client.get("/api/local/status")
    assert response.status_code == 200
    response_json = json.loads(response.text)
    assert response_json["localhost_qualified"]["qualified"] is False
    assert response_json["localhost_qualified"]["errors"] == [
        "The node does not have a sufficient number of CPU cores. Required: 2, Actual: 1.",
        "The node does not have a sufficient memory. Required: 2, Actual: 1.",
        "The node does not have sufficient space on the root disk. Required: 10, Actual: 1.",
    ]
