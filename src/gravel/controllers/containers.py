# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
import shlex

from gravel.controllers.errors import GravelError
from gravel.controllers.utils import aqr_run_cmd


class ContainerError(GravelError):
    pass


class ContainerPullError(ContainerError):
    pass


async def container_pull(registry: str, image: str, secure: bool) -> str:
    tlsstr = "" if secure else "--tls-verify=false"
    imgstr = f"docker://{registry}/{image}"

    cmdstr = f"podman pull -q {imgstr} {tlsstr}"
    ret, out, err = await aqr_run_cmd(shlex.split(cmdstr))
    if ret != 0:
        raise ContainerPullError(msg=err)
    if out is None or len(out) == 0:
        raise ContainerPullError(msg="unable to obtain container hash")

    return out
