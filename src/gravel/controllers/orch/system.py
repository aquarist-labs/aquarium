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
import socket
import subprocess
from pathlib import Path

from gravel.controllers.errors import GravelError


class SystemCtlError(GravelError):
    pass


class HostnameCtlError(GravelError):
    pass


def set_ntp(addr: str) -> bool:
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
        raise SystemCtlError("Unable to restart unit 'chronyd.service'.") from e
    return True


def set_hostname(name: str) -> bool:
    old_hostname = socket.gethostname()

    try:
        cmd = ["hostnamectl", "set-hostname", name]
        subprocess.check_output(cmd, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise HostnameCtlError(f"Unable to set hostname to '{name}'.") from e

    with open("/etc/hosts", "r+") as f:
        text = f.read()
        f.seek(0)
        f.truncate(0)
        f.write(text.replace(old_hostname, name))

    return True
