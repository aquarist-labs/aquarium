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

from pathlib import Path
import logging

from libaqua.errors import (
    BuildsPathNotFoundError,
    DeploymentNotFoundError,
    DeploymentPathNotFoundError,
    RootNotFoundError
)


logger: logging.Logger = logging.getLogger("aquarium")


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
