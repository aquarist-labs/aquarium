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

import os
from logging import Logger
from pathlib import Path

from fastapi.logger import logger as fastapi_logger
from gravel.controllers.nodes.errors import NodeChronyRestartError
from gravel.controllers.utils import aqr_run_cmd

logger: Logger = fastapi_logger

FILE_PATH = "/etc/chrony.d"
CONFIG_FILE = "aquarium.conf"


async def set_ntp_addr(addr: str) -> None:
    Path(FILE_PATH).mkdir(parents=True, exist_ok=True)

    for f in os.listdir(FILE_PATH):
        os.remove(os.path.join(FILE_PATH, f))

    ntp_server = "server {} iburst\n".format(addr)
    with open(os.path.join(FILE_PATH, CONFIG_FILE), "w") as f:
        f.write(ntp_server)

    ret, _, err = await aqr_run_cmd(["systemctl", "restart", "chronyd.service"])
    if ret:
        raise NodeChronyRestartError(
            f"Unable to restart chronyd.service: {err}"
        )
    logger.info("NTP address set")
