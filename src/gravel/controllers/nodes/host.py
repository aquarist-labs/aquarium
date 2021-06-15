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

import socket
import subprocess

from gravel.controllers.errors import GravelError


class HostnameCtlError(GravelError):
    pass


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
