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

# pyright: reportPrivateUsage=false, reportUnknownMemberType=false
# pyright: reportMissingTypeStubs=false


from typing import Callable, List, cast
import pytest
from pytest_mock import MockerFixture
from pyfakefs import fake_filesystem

from gravel.controllers.gstate import GlobalState
from gravel.tests.unit.asyncio import FakeProcess


def test_bootstrap_process(mocker: MockerFixture) -> None:
    async def mock_subprocess(*args: List[str]) -> FakeProcess:
        assert len(args) > 0
        assert "foo" in args
        return FakeProcess(stdout=None, stderr=None, ret=0)

    mocker.patch("asyncio.create_subprocess_exec", new=mock_subprocess)
    from gravel.controllers.nodes.etcd import _bootstrap_etcd_process

    _bootstrap_etcd_process(["foo", "bar"])


@pytest.mark.asyncio
async def test_spawn_etcd(
    mocker: MockerFixture,
    fs: fake_filesystem.FakeFilesystem,
    gstate: GlobalState,
) -> None:
    class FakeProcessCtx:
        pid = 1234

        def __init__(
            self, target: Callable[[List[str]], None], args: List[str]
        ) -> None:
            assert target is not None
            assert len(args) > 0

        def start(self) -> None:
            pass

    async def mock_subprocess(*args: List[str]) -> FakeProcess:
        assert len(args) > 0
        assert "podman" in args
        return FakeProcess(stdout=None, stderr=None, ret=0)

    import multiprocessing.context

    mocker.patch.object(
        multiprocessing.context.SpawnContext, "Process", new=FakeProcessCtx
    )
    mocker.patch("asyncio.create_subprocess_exec", new=mock_subprocess)
    from gravel.controllers.nodes.etcd import spawn_etcd

    fs.makedirs("/var/lib")
    await spawn_etcd(gstate, True, "asd-fgh-jkl", "foobar", "1.1.1.1")
    assert fs.exists(gstate.config.options.etcd.data_dir)


def assert_pull_image(
    *args: List[str], stdout: int, stderr: int, registry: str, version: str
) -> None:
    import asyncio

    assert len(args) > 0
    assert args[0] == "podman"
    assert args[1] == "pull"
    assert len(args[2]) > 0
    image = cast(str, args[2]).split(":")
    assert len(image) == 2
    assert image[0] == registry
    assert image[1] == version
    assert stdout == asyncio.subprocess.PIPE
    assert stderr == asyncio.subprocess.PIPE


@pytest.mark.asyncio
async def test_etcd_pull_image(
    mocker: MockerFixture, gstate: GlobalState
) -> None:
    async def mock_subprocess(
        *args: List[str], stdout: int, stderr: int
    ) -> FakeProcess:
        assert_pull_image(
            *args,
            stdout=stdout,
            stderr=stderr,
            registry=gstate.config.options.etcd.registry,
            version=gstate.config.options.etcd.version,
        )
        return FakeProcess(stdout="", stderr="", ret=0)

    mocker.patch("asyncio.create_subprocess_exec", new=mock_subprocess)
    from gravel.controllers.nodes.etcd import etcd_pull_image

    await etcd_pull_image(gstate)


@pytest.mark.asyncio
async def test_fail_etcd_pull_image(
    mocker: MockerFixture, gstate: GlobalState
) -> None:
    async def mock_subprocess(
        *args: List[str], stdout: int, stderr: int
    ) -> FakeProcess:
        assert_pull_image(
            *args,
            stdout=stdout,
            stderr=stderr,
            registry=gstate.config.options.etcd.registry,
            version=gstate.config.options.etcd.version,
        )
        return FakeProcess(stdout=None, stderr="foobar", ret=1)

    mocker.patch("asyncio.create_subprocess_exec", new=mock_subprocess)
    from gravel.controllers.nodes.etcd import (
        etcd_pull_image,
        ContainerFetchError,
    )

    try:
        await etcd_pull_image(gstate)
    except ContainerFetchError as e:
        assert e.message == "foobar"
