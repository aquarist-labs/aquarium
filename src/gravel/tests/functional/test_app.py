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


import pytest


@pytest.mark.asyncio
async def test_simple_app_response(async_client):
    response = await async_client.get("/api/local/status")
    assert response.status_code == 200
    assert '{"inited":false,"node_stage":0}' == response.text
    import asyncio

    await asyncio.sleep(5)

    response = await async_client.get("/api/local/status")
    assert response.status_code == 200
    assert '{"inited":true,"node_stage":0}' == response.text
