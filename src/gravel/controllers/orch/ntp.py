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
import subprocess
from pathlib import Path


def set_address(addr: str) -> bool:
    file_path = "/etc/chrony.d"
    config_file = "aquarium.conf"
    Path(file_path).mkdir(parents=True, exist_ok=True)

    for f in os.listdir(file_path):
        os.remove(os.path.join(file_path, f))

    ntp_server = "server {} iburst\n".format(addr)
    with open(os.path.join(file_path, config_file), "w") as f:
        f.write(ntp_server)

    restart_cmd = ["systemctl", "restart", "chronyd.service"]
    try:
        subprocess.check_output(restart_cmd, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise ChronyRestartError("Unable to restart chronyd.service") from e
    return True


class ChronyRestartError(Exception):
    pass
