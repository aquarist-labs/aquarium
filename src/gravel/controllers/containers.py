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
from typing import Any, Dict, MutableMapping, Optional

import requests
import toml

from gravel.controllers.errors import GravelError
from gravel.controllers.utils import aqr_run_cmd

REGISTRIES_CONF = "/etc/containers/registries.conf"


class ContainerError(GravelError):
    pass


class ContainerPullError(ContainerError):
    pass


class ContainerRegistryError(ContainerError):
    registry: str

    def __init__(self, registry: str, msg: Optional[str] = None) -> None:
        super().__init__(msg)
        self.registry = registry


class UnknownRegistryError(ContainerRegistryError):
    pass


class RegistrySecurityError(ContainerRegistryError):
    pass


class ContainerImageError(ContainerError):
    image: str

    def __init__(self, image: str, msg: Optional[str] = None) -> None:
        super().__init__(msg)
        self.image = image


class ImageNameError(ContainerImageError):
    pass


class UnknownImageError(ContainerImageError):
    pass


class UnknownImageTagError(ContainerImageError):
    pass


async def registry_check(registry: str, image: str, secure: bool) -> None:

    proto = "https" if secure else "http"
    # check for an existing registry
    #
    try:
        req = requests.get(f"{proto}://{registry}/v2/")
        if req.status_code != requests.codes.ok:
            raise UnknownRegistryError(
                registry,
                msg=f"Error connecting to registry at '{registry}: {req.text}",
            )
    except requests.exceptions.SSLError:
        req_proto = "https" if not secure else "http"
        raise RegistrySecurityError(
            registry,
            msg=f"Registry at '{registry}' requires an {req_proto} connection.",
        )
    except requests.exceptions.ConnectionError as e:
        raise UnknownRegistryError(
            registry,
            msg=f"Error connecting to registry at '{registry}': {str(e)}",
        )

    # check for image:tag
    #
    img = image.split(":")
    if len(img) != 2:
        raise ImageNameError(image, msg="Missing tag information from image.")
    (imgname, imgtag) = img

    try:
        req = requests.get(f"{proto}://{registry}/v2/{imgname}/tags/list")
    except Exception as e:
        raise ContainerError(msg=str(e))

    if req.status_code != requests.codes.ok:
        raise UnknownImageError(
            imgname, msg=f"Could not find image '{imgname}'."
        )
    res = req.json()
    assert res["name"] == imgname
    if imgtag not in res["tags"]:
        raise UnknownImageTagError(
            image, msg=f"Could not find image '{imgname}' with tag '{imgtag}'."
        )


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
