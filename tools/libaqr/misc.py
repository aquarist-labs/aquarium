# project aquarium's testing battery
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
from pathlib import Path
import subprocess
import shlex
from typing import List, Optional
import logging

from libaqr.errors import (
    AqrError,
    BoxAlreadyExistsError,
    BuildsPathNotFoundError,
    DeploymentNotFoundError,
    DeploymentPathNotFoundError,
    ImageNotFoundError,
    RootNotFoundError
)


logger: logging.Logger = logging.getLogger("aquarium")


def list_boxes() -> List[str]:
    """ List all known vagrant boxes. Includes non-aquarium related boxes. """
    proc = subprocess.run(
        shlex.split("vagrant box list --machine-readable"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout = proc.stdout.decode("utf-8")
    stderr = proc.stderr.decode("utf-8")
    if proc.returncode != 0:
        logger.error(f"error running vagrant: {stderr}")

    logger.debug(f"boxes: {stdout}")

    boxes = [name for name in stdout.splitlines() if name.count("box-name") > 0]
    boxnames = [entry.split(",")[3] for entry in boxes]
    return boxnames


def remove_box(name: str) -> None:
    """ Remove an existing box """
    boxes = list_boxes()
    if name not in boxes:
        return

    cmd = f"vagrant box remove {name}"
    proc = subprocess.run(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8")
        raise AqrError(f"error removing box '{name}': {stderr}")


def import_image(buildspath: Path, imgname: str) -> None:
    """ Import an image as a vagrant box with the same name. """
    avail_boxes = list_boxes()
    if imgname in avail_boxes:
        raise BoxAlreadyExistsError()

    imgbuild = buildspath.joinpath(imgname)
    if not imgbuild.exists():
        raise ImageNotFoundError(f"build for image '{imgname}' not found")

    outpath = imgbuild.joinpath("_out")
    if not outpath:
        raise ImageNotFoundError(f"image '{imgname}' not built")

    outfiles = [entry for entry in next(os.walk(outpath))[2]]
    found: Optional[str] = None
    for file in outfiles:
        if file.count(".vagrant.") > 0 and file.endswith(".box"):
            found = file
            break

    if not found:
        raise ImageNotFoundError(f"image '{imgname}' not found at {outpath}")

    imgpath: Path = outpath.joinpath(found)
    assert imgpath.exists()

    boxname = imgname
    cmd = f"vagrant box add {boxname} {imgpath}"
    logger.debug(f"adding box {boxname} from image at {imgpath}")
    proc = subprocess.run(
        shlex.split(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stderr = proc.stdout.decode("utf-8")
    if proc.returncode != 0:
        raise BaseException(f"error adding vagrant box: {stderr}")


def list_images() -> List[str]:
    """ List all built Vagrant images """
    rootdir = find_root()
    imagepath = rootdir.joinpath("images")
    buildspath = imagepath.joinpath("build")
    if not buildspath.exists():
        return []

    def is_vagrant_img(path: Path) -> bool:
        assert path.exists()
        outdir = path.joinpath("_out")
        if not outdir.exists():
            raise FileNotFoundError()

        rawimg: Optional[Path] = None
        img: Optional[Path] = None
        for entry in next(os.walk(outdir))[2]:
            if not entry.startswith("project-aquarium"):
                continue

            imgpath = Path(entry)
            if imgpath.suffix == ".raw":
                rawimg = imgpath

            elif imgpath.suffix == ".box":
                if entry.count("vagrant") > 0:
                    img = imgpath

        if not rawimg:
            raise FileNotFoundError()
        elif not img:
            return False

        return True

    images: List[str] = []
    for build in next(os.walk(buildspath))[1]:
        if build.startswith("."):
            continue

        try:
            ret = is_vagrant_img(buildspath.joinpath(build))
        except FileNotFoundError:
            logger.debug(f"build {build} not a vagrant build")
            continue

        if not ret:
            logger.debug(f"build {build} not a vagrant build")
            continue

        images.append(build)

    return images


def find_root() -> Path:
    cwd = Path.cwd()

    def git_exists(path: Path) -> bool:
        gitpath = path.joinpath(".git")
        return gitpath.exists() and gitpath.is_dir()

    while cwd.as_posix() != "/":
        if git_exists(cwd):
            return cwd
        cwd = cwd.parent

    raise RootNotFoundError()


def find_builds_path() -> Path:
    try:
        rootdir = find_root()
    except RootNotFoundError:
        raise BuildsPathNotFoundError("unable to find root")

    builds: Path = rootdir.joinpath("images/build")
    if not builds.exists():
        raise BuildsPathNotFoundError()
    return builds


def find_deployments_path() -> Path:
    try:
        rootdir = find_root()
    except FileNotFoundError:
        raise DeploymentPathNotFoundError("unable to find root")

    vagrantdir = rootdir.joinpath("tests/vagrant")
    setupsdir = vagrantdir.joinpath("deployments")
    if not setupsdir:
        raise DeploymentPathNotFoundError("unable to find deployments dir")
    return setupsdir


def get_deployment_path(name: str) -> Path:
    """ Obtain path to deployment `name` """
    deployments_path = find_deployments_path()
    assert deployments_path.exists()
    deployment = deployments_path.joinpath(name)
    if not deployment.exists():
        raise DeploymentNotFoundError(f"unable to find deployment '{name}'")
    return deployment
