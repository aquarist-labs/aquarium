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
        '{"localhost_qualified":{"all_qualified":true,"cpu_qualified":{"qualified":true,"min_cpu":2,"actual_cpu":8,"error":"","status":0},"mem_qualified":{"qualified":true,"min_mem":2,"actual_mem":31,"error":"","status":0},"root_disk_qualified":{"qualified":true,"min_disk":10,"actual_disk":18,"error":"","status":0}},"inited":false,"node_stage":0}'
        == response.text
    )

    import asyncio

    await asyncio.sleep(5)

    response = await async_client.get("/api/local/status")
    assert response.status_code == 200
    assert (
        '{"localhost_qualified":{"all_qualified":true,"cpu_qualified":{"qualified":true,"min_cpu":2,"actual_cpu":8,"error":"","status":0},"mem_qualified":{"qualified":true,"min_mem":2,"actual_mem":31,"error":"","status":0},"root_disk_qualified":{"qualified":true,"min_disk":10,"actual_disk":18,"error":"","status":0}},"inited":true,"node_stage":0}'
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
    assert response_json["localhost_qualified"]["all_qualified"] is True
    assert (
        response_json["localhost_qualified"]["cpu_qualified"]["qualified"]
        is True
    )
    assert response_json["localhost_qualified"]["cpu_qualified"]["min_cpu"] == 2
    assert (
        response_json["localhost_qualified"]["cpu_qualified"]["actual_cpu"] == 8
    )
    assert response_json["localhost_qualified"]["cpu_qualified"]["error"] == ""
    assert response_json["localhost_qualified"]["cpu_qualified"]["status"] == 0
    assert (
        response_json["localhost_qualified"]["mem_qualified"]["qualified"]
        is True
    )
    assert response_json["localhost_qualified"]["mem_qualified"]["min_mem"] == 2
    assert (
        response_json["localhost_qualified"]["mem_qualified"]["actual_mem"]
        == 31
    )
    assert response_json["localhost_qualified"]["mem_qualified"]["error"] == ""
    assert response_json["localhost_qualified"]["mem_qualified"]["status"] == 0
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"]["qualified"]
        is True
    )
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"]["min_disk"]
        == 10
    )
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"][
            "actual_disk"
        ]
        == 18
    )
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"]["error"]
        == ""
    )
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"]["status"]
        == 0
    )

    # Failed CPU count
    mocker.patch("psutil.cpu_count", return_value=1)
    mocker.patch(
        "psutil.virtual_memory", return_value=FakeMemory(total=33498816512)
    )
    mocker.patch("psutil.disk_usage", return_value=FakeDisk(total=20000000000))

    response = await async_client.get("/api/local/status")
    assert response.status_code == 200
    response_json = json.loads(response.text)
    assert response_json["localhost_qualified"]["all_qualified"] is False
    assert (
        response_json["localhost_qualified"]["cpu_qualified"]["qualified"]
        is False
    )
    assert response_json["localhost_qualified"]["cpu_qualified"]["min_cpu"] == 2
    assert (
        response_json["localhost_qualified"]["cpu_qualified"]["actual_cpu"] == 1
    )
    assert response_json["localhost_qualified"]["cpu_qualified"]["error"] == (
        "The node does not have a sufficient number of CPU cores. Required: 2, Actual: 1."
    )
    assert response_json["localhost_qualified"]["cpu_qualified"]["status"] == 1
    assert (
        response_json["localhost_qualified"]["mem_qualified"]["qualified"]
        is True
    )
    assert response_json["localhost_qualified"]["mem_qualified"]["min_mem"] == 2
    assert (
        response_json["localhost_qualified"]["mem_qualified"]["actual_mem"]
        == 31
    )
    assert response_json["localhost_qualified"]["mem_qualified"]["error"] == ""
    assert response_json["localhost_qualified"]["mem_qualified"]["status"] == 0
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"]["qualified"]
        is True
    )
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"]["min_disk"]
        == 10
    )
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"][
            "actual_disk"
        ]
        == 18
    )
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"]["error"]
        == ""
    )
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"]["status"]
        == 0
    )

    # Everything fails
    mocker.patch("psutil.cpu_count", return_value=1)
    mocker.patch(
        "psutil.virtual_memory", return_value=FakeMemory(total=1073741824)
    )
    mocker.patch("psutil.disk_usage", return_value=FakeDisk(total=1073741824))

    response = await async_client.get("/api/local/status")
    assert response.status_code == 200
    response_json = json.loads(response.text)
    assert response_json["localhost_qualified"]["all_qualified"] is False
    assert (
        response_json["localhost_qualified"]["cpu_qualified"]["qualified"]
        is False
    )
    assert response_json["localhost_qualified"]["cpu_qualified"]["min_cpu"] == 2
    assert (
        response_json["localhost_qualified"]["cpu_qualified"]["actual_cpu"] == 1
    )
    assert response_json["localhost_qualified"]["cpu_qualified"]["error"] == (
        "The node does not have a sufficient number of CPU cores. Required: 2, Actual: 1."
    )
    assert response_json["localhost_qualified"]["cpu_qualified"]["status"] == 1
    assert (
        response_json["localhost_qualified"]["mem_qualified"]["qualified"]
        is False
    )
    assert response_json["localhost_qualified"]["mem_qualified"]["min_mem"] == 2
    assert (
        response_json["localhost_qualified"]["mem_qualified"]["actual_mem"] == 1
    )
    assert response_json["localhost_qualified"]["mem_qualified"]["error"] == (
        "The node does not have a sufficient memory. Required: 2, Actual: 1."
    )
    assert response_json["localhost_qualified"]["mem_qualified"]["status"] == 1
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"]["qualified"]
        is False
    )
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"]["min_disk"]
        == 10
    )
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"][
            "actual_disk"
        ]
        == 1
    )
    assert response_json["localhost_qualified"]["root_disk_qualified"][
        "error"
    ] == (
        "The node does not have sufficient space on the root disk. Required: 10, Actual: 1."
    )
    assert (
        response_json["localhost_qualified"]["root_disk_qualified"]["status"]
        == 1
    )
