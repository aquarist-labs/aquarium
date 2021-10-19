# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
import shlex
from pathlib import Path
from typing import Any, Dict, MutableMapping

import toml

from gravel.controllers.errors import GravelError
from gravel.controllers.utils import aqr_run_cmd

REGISTRIES_CONF = "/etc/containers/registries.conf"


class ContainerError(GravelError):
    pass


class ContainerPullError(ContainerError):
    pass


async def container_pull(registry: str, image: str) -> str:
    imgstr = f"docker://{registry}/{image}"
    cmdstr = f"podman pull -q {imgstr}"
    ret, out, err = await aqr_run_cmd(shlex.split(cmdstr))
    if ret != 0:
        raise ContainerPullError(msg=err)
    if out is None or len(out) == 0:
        raise ContainerPullError(msg="unable to obtain container hash")
    return out


async def get_registries_conf() -> MutableMapping[str, Any]:
    path = Path(REGISTRIES_CONF)
    if not path.exists():
        return {}

    with path.open("r"):
        try:
            data = toml.load(path)
        except toml.TomlDecodeError:
            raise ContainerError("error decoding registries conf")
        except Exception:
            raise ContainerError("unknown error loading registries conf")
        return data


async def set_registry(url: str, secure: bool) -> None:
    path = Path(REGISTRIES_CONF)
    data: Dict[str, Any] = {
        "registries": {
            "search": {
                "registries": [url],
            },
        },
    }
    if not secure:
        data["registries"]["insecure"] = {
            "registries": [url],
        }

    with path.open("w") as fd:
        try:
            toml.dump(data, fd)
        except Exception:
            raise ContainerError("unknown error writing registries conf")
