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

import asyncio
import multiprocessing
from pathlib import Path
import shlex
from typing import List, Optional
from logging import Logger
from fastapi.logger import logger as fastapi_logger

from gravel.controllers.gstate import GlobalState
from gravel.controllers.errors import GravelError


class ContainerFetchError(GravelError):
    pass


logger: Logger = fastapi_logger


# We need to rely on "spawn" because otherwise the subprocess' signal
# handler will play nasty tricks with uvicorn's and fastapi's signal
# handlers.
# For future reference,
# - uvicorn issue: https://github.com/encode/uvicorn/issues/548
# - python bug report: https://bugs.python.org/issue43064
# - somewhat of a solution, using "spawn" for multiprocessing:
# https://github.com/tiangolo/fastapi/issues/1487#issuecomment-657290725
#
# And because we need to rely on spawn, which will create a new python
# interpreter to execute what we are specifying, the function we're passing
# needs to be pickled. And nested functions, apparently, can't be pickled. Thus,
# we need to have the functions at the top-level scope.
#
def _bootstrap_etcd_process(cmd: List[str]):
    async def _run_etcd():
        process = await asyncio.create_subprocess_exec(*cmd)
        await process.wait()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_etcd())
    except KeyboardInterrupt:
        pass


async def spawn_etcd(
    gstate: GlobalState,
    new: bool,
    token: Optional[str],
    hostname: str,
    address: str,
    initial_cluster: Optional[str] = None,
) -> None:

    assert hostname
    assert address

    data_dir: Path = Path(gstate.config.options.etcd.data_dir)
    if not data_dir.exists():
        data_dir.mkdir(0o700)

    logger.info(f"starting etcd, hostname: {hostname}, addr: {address}")

    def _get_etcd_args() -> List[str]:
        client_url: str = f"http://{address}:2379"
        peer_url: str = f"http://{address}:2380"

        nonlocal initial_cluster
        if not initial_cluster:
            initial_cluster = f"{hostname}={peer_url}"

        args: List[str] = [
            "--name",
            hostname,
            "--initial-advertise-peer-urls",
            peer_url,
            "--listen-peer-urls",
            peer_url,
            "--listen-client-urls",
            f"{client_url},http://127.0.0.1:2379",
            "--advertise-client-urls",
            client_url,
            "--initial-cluster",
            initial_cluster,
            "--data-dir",
            str(data_dir),
        ]

        if new:
            assert token
            args += ["--initial-cluster-state", "new"]
            args += ["--initial-cluster-token", token]
        else:
            args += ["--initial-cluster-state", "existing"]

        return args

    def _get_container_cmd() -> List[str]:
        registry = gstate.config.options.etcd.registry
        version = gstate.config.options.etcd.version

        return [
            "podman",
            "run",
            "--rm",
            "--replace",
            "--net=host",
            "--entrypoint",
            "/usr/local/bin/etcd",
            "-v",
            f"{data_dir}:{data_dir}",
            "--name",
            f"etcd.{hostname}",
            f"{registry}:{version}",
        ] + _get_etcd_args()

    cmd = _get_container_cmd()

    ctx = multiprocessing.get_context("spawn")
    logger.debug("spawn etcd: " + shlex.join(cmd))
    process = ctx.Process(target=_bootstrap_etcd_process, args=(cmd,))
    process.start()

    logger.info(f"started etcd process pid = {process.pid}")
    await gstate.init_store()


async def etcd_pull_image(gstate: GlobalState) -> None:
    registry = gstate.config.options.etcd.registry
    version = gstate.config.options.etcd.version

    logger.debug(f"fetching etcd image from {registry}:{version}")

    cmd = shlex.split(f"podman pull {registry}:{version}")
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        # wait for 5 minutes
        retcode = await asyncio.wait_for(process.wait(), 300)
        if retcode != 0:
            stderr = "unknown error"
            if process.stderr:
                stderr = (await process.stderr.read()).decode("utf-8")
            raise ContainerFetchError(stderr)
    except TimeoutError:
        raise ContainerFetchError("timed out")
