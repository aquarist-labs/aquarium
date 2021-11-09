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
import requests
import requests_mock

from gravel.controllers.containers import (
    ImageNameError,
    RegistrySecurityError,
    UnknownImageError,
    UnknownImageTagError,
    UnknownRegistryError,
    registry_check,
)


@pytest.mark.asyncio
async def test_registry_check_existing(
    requests_mock: requests_mock.Mocker,
) -> None:
    requests_mock.get("http://secure.bar/v2/", exc=requests.exceptions.SSLError)
    requests_mock.get("https://secure.bar/v2/")
    requests_mock.get("http://insecure.bar/v2/")
    requests_mock.get(
        "https://insecure.bar/v2/", exc=requests.exceptions.SSLError
    )
    requests_mock.get(
        "https://dne.tld/v2/", exc=requests.exceptions.ConnectionError
    )

    imgres = {
        "name": "image/name",
        "tags": ["tag"],
    }
    requests_mock.get("https://secure.bar/v2/image/name/tags/list", json=imgres)
    requests_mock.get(
        "http://insecure.bar/v2/image/name/tags/list", json=imgres
    )

    raised = False
    await registry_check("secure.bar", "image/name:tag", True)
    try:
        await registry_check("secure.bar", "image/name:tag", False)
    except RegistrySecurityError:
        raised = True
    assert raised

    raised = False
    await registry_check("insecure.bar", "image/name:tag", False)
    try:
        await registry_check("insecure.bar", "image/name:tag", True)
    except RegistrySecurityError:
        raised = True
    assert raised

    raised = False
    try:
        await registry_check("dne.tld", "image/name:tag", True)
    except UnknownRegistryError:
        raised = True
    assert raised


@pytest.mark.asyncio
async def test_registry_check_image(
    requests_mock: requests_mock.Mocker,
) -> None:
    res = {
        "name": "image/name",
        "tags": ["tag"],
    }
    requests_mock.get("https://secure.tld/v2/")
    requests_mock.get("https://secure.tld/v2/image/name/tags/list", json=res)
    requests_mock.get(
        "https://secure.tld/v2/image/dne/tags/list", status_code=404
    )

    await registry_check("secure.tld", "image/name:tag", True)

    raised = False
    try:
        await registry_check("secure.tld", "image/name", True)
    except ImageNameError:
        raised = True
    assert raised

    raised = False
    try:
        await registry_check("secure.tld", "image/dne:tag", True)
    except UnknownImageError:
        raised = True
    assert raised

    raised = False
    try:
        await registry_check("secure.tld", "image/name:dne", True)
    except UnknownImageTagError:
        raised = True
    assert raised
