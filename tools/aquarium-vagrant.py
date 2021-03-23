#!/usr/bin/env python3
#
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
import sys
import errno
import json
from typing import Any, Dict, List, Optional, Tuple
import click
import logging
import subprocess
import shlex
import shutil
from click.decorators import make_pass_decorator
from pathlib import Path
from datetime import datetime as dt
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger("aquarium")


class BaseError(Exception):
    _msg: str

    def __init__(self, msg: str = ""):
        self._msg = msg

    @property
    def message(self) -> str:
        return self._msg


class BoxAlreadyExistsError(BaseError):
    pass


class BuildsPathNotFoundError(BaseError):
    pass


class RootNotFoundError(BaseError):
    pass


class ImageNotFoundError(BaseError):
    pass


class DeploymentPathNotFoundError(BaseError):
    pass


class DeploymentExistsError(BaseError):
    pass


class DeploymentNotFoundError(BaseError):
    pass


class DeploymentNotFinishedError(BaseError):
    pass


class EnterDeploymentError(BaseError):
    pass


class DeploymentModel(BaseModel):
    name: str
    created_on: str


class AppCtx:

    _json_output: bool

    def __init__(self, json_output: bool):
        self._json_output = json_output
        pass

    @property
    def json(self) -> bool:
        return self._json_output


pass_appctx = make_pass_decorator(AppCtx)


def _find_root() -> Path:
    cwd = Path.cwd()

    def git_exists(path: Path) -> bool:
        gitpath = path.joinpath(".git")
        return gitpath.exists() and gitpath.is_dir()

    while cwd.as_posix() != "/":
        if git_exists(cwd):
            return cwd
        cwd = cwd.parent

    raise RootNotFoundError()


def _find_builds_path() -> Path:
    try:
        rootdir = _find_root()
    except RootNotFoundError:
        raise BuildsPathNotFoundError("unable to find root")

    builds: Path = rootdir.joinpath("images/build")
    if not builds.exists():
        raise BuildsPathNotFoundError()
    return builds


def _find_deployments_path() -> Path:
    try:
        rootdir = _find_root()
    except FileNotFoundError:
        raise DeploymentPathNotFoundError("unable to find root")

    vagrantdir = rootdir.joinpath("tests/vagrant")
    setupsdir = vagrantdir.joinpath("deployments")
    if not setupsdir:
        raise DeploymentPathNotFoundError("unable to find deployments dir")
    return setupsdir


def _get_deployment_path(name: str) -> Path:
    """ Obtain path to deployment `name` """
    deployments = _list_deployments()
    if name not in deployments:
        raise DeploymentNotFoundError(f"unable to find deployment '{name}'")

    deployments_path = _find_deployments_path()
    assert deployments_path.exists()
    deployment = deployments_path.joinpath(name)
    assert deployment.exists()
    return deployment


@click.group()
@click.option("-d", "--debug", flag_value=True)
@click.option("--json", flag_value=True)
@click.pass_context
def app(ctx: click.Context, debug: bool, json: bool) -> None:

    if debug:
        logger.setLevel(logging.DEBUG)

    logger.debug(f"app => debug: {debug}, ctx: {ctx}")
    ctx.obj = AppCtx(json_output=json)


def _list_boxes() -> List[str]:
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


def _list_images() -> List[str]:
    """ List all built Vagrant images """
    try:
        rootdir = _find_root()
    except FileNotFoundError:
        logger.error("couldn't find git root tree")
        sys.exit(1)

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


def _list_deployments() -> List[str]:
    """ List all existing Aquarium's Vagrant deployments. """
    try:
        rootdir = _find_root()
    except FileNotFoundError:
        logger.error("unable to find git's root dir")
        sys.exit(1)

    vagrantdir = rootdir.joinpath("tests/vagrant")
    setupsdir = vagrantdir.joinpath("deployments")
    if not vagrantdir.exists() or not setupsdir.exists():
        return []

    setups = [entry for entry in next(os.walk(setupsdir))[1]]
    return setups


def _import_image(imgname: str) -> None:
    """ Import an image as a vagrant box with the same name. """
    avail_boxes = _list_boxes()
    if imgname in avail_boxes:
        raise BoxAlreadyExistsError()

    try:
        buildspath: Path = _find_builds_path()
    except BuildsPathNotFoundError:
        raise ImageNotFoundError("no available builds")

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


def _remove_box(name: str) -> None:
    """ Remove an existing box """
    boxes = _list_boxes()
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
        raise BaseError(f"error removing box '{name}': {stderr}")


def _remove(name: str) -> None:
    """ Remove an existing deployment """

    try:
        deployment = _get_deployment_path(name)
    except DeploymentNotFoundError:
        return

    if not deployment.exists():
        return

    shutil.rmtree(deployment)


def _create(name: str, box: str) -> None:
    """ Create a new deployment, based on provided box. """
    rootdir = _find_root()
    assert rootdir.exists()

    deployment_path = _find_deployments_path()
    if not deployment_path.exists():
        deployment_path.mkdir()
    assert deployment_path.exists()

    template_path = deployment_path.parent.joinpath("templates")
    assert template_path.exists()

    template = template_path.joinpath("Vagrantfile.tmpl")
    assert template.exists()

    deployments = _list_deployments()
    boxes = _list_boxes()
    assert name not in deployments
    assert box in boxes

    new_deployment = deployment_path.joinpath(name)
    if new_deployment.exists():
        logger.error(f"deployment {name} already exists")
        raise DeploymentExistsError()

    try:
        logger.debug(f"creating new deployment at '{new_deployment}'")
        new_deployment.mkdir()
    except Exception as e:
        logger.error(
            f"unable to create deployment at {new_deployment}: {str(e)}"
        )
        raise BaseError(f"error creating deployment: {str(e)}")

    logger.debug(f"reading template from '{template_path}'")
    template_text = template.read_text()
    vagrantfile_text = template_text.format(BOXNAME=box, ROOTDIR=rootdir)

    vagrantfile = new_deployment.joinpath("Vagrantfile")
    logger.debug(f"writing vagrantfile at '{vagrantfile}'")
    vagrantfile.write_text(vagrantfile_text)

    now = dt.now()
    datefile = new_deployment.joinpath("created_on")
    datefile.write_text(now.isoformat())


#
# create and remove setups
#
@app.command("create")
@click.option("-b", "--box", type=str, required=False)
@click.option("-i", "--image", type=str, required=False)
@click.option("-f", "--force", flag_value=True)
@click.argument("name", required=True, type=str)
@pass_appctx
def cmd_create(
    ctx: AppCtx,
    name: str,
    box: Optional[str],
    image: Optional[str],
    force: bool
) -> None:
    logger.debug(f"create: ctx = {ctx}, name: {name}, box: {box}, img: {image}")

    avail_images = _list_images()
    avail_boxes = _list_boxes()
    avail_deployments = _list_deployments()

    remove_existing_deployment = False

    if name in avail_deployments:
        if not force:
            click.secho(f"Deployment '{name}' already exists", fg="red")
            sys.exit(errno.EEXIST)
        remove_existing_deployment = True

    if not box and not image:
        box = "aquarium"
    elif not box and image:
        if image not in avail_images:
            click.secho(f"Image '{image}' not found", fg="red")
            sys.exit(errno.ENOENT)

        if image in avail_boxes and force:
            # remove existing box first
            try:
                _remove_box(image)
            except BaseError as e:
                logger.error(
                    f"Unable to remove existing box '{image}': {e.message}"
                )
                sys.exit(1)
        try:
            click.secho(f"Importing image '{image}' as Vagrant box", fg="cyan")
            _import_image(image)
            avail_boxes.append(image)
            box = image
            click.secho(f"Imported image '{image}' as Vagrant box", fg="green")
        except ImageNotFoundError as e:
            click.secho(f"Error importing image '{image}': {e.message}")
            sys.exit(1)
    elif box and image:
        click.secho("Please provide only one of '--box' or '--image'", fg="red")
        sys.exit(errno.EINVAL)

    assert box is not None
    if box not in avail_boxes:
        click.secho(f"Unable to find box '{box}'", fg="red")
        return

    if remove_existing_deployment:
        click.secho(f"Removing existing deployment '{name}'")
        try:
            _remove(name)
        except BaseError as e:
            logger.error(f"error removing deployment '{name}': {e.message}")
        click.secho(f"Removed deployment '{name}'")

    try:
        _create(name, box)
    except Exception as e:
        click.secho(
            f"Error creating deployment '{name}' from box '{box}': {str(e)}",
            fg="red"
        )
        raise e
        sys.exit(1)
    click.secho("success!", fg="green")


@app.command("remove")
@click.argument("name", required=True, type=str)
@pass_appctx
def cmd_remove(ctx: AppCtx, name: str) -> None:
    logger.debug(f"remove => name: {name}, ctx: {ctx}")
    click.secho(f"Removing deployment '{name}'", fg="cyan")
    _remove(name)
    click.secho("Removed.", fg="green")


#
# list images and boxes
#
@app.group("list")
def cmd_list() -> None:
    logger.debug("list")
    pass


def print_entry(name: str) -> None:
    """ Print an entry in the format '* NAME', with pretty colors """
    print("{} {}".format(
        click.style("*", fg="cyan"),
        click.style(name, fg="white", bold=True)
    ))


def print_json(what: Any) -> None:
    print(json.dumps(what))


@cmd_list.command("images")
@pass_appctx
def cmd_list_images(ctx: AppCtx) -> None:
    logger.debug("list images")
    images = _list_images()
    if len(images) == 0:
        click.secho("No images found", fg="cyan")
        return

    if ctx.json:
        print_json(images)
        return

    for image in images:
        print_entry(image)


@cmd_list.command("boxes")
@pass_appctx
def cmd_list_boxes(ctx: AppCtx) -> None:
    logger.debug("list boxes")
    boxes = _list_boxes()
    if len(boxes) == 0:
        click.secho("No boxes found", fg="cyan")
        return

    if ctx.json:
        print_json(boxes)
        return

    for boxname in boxes:
        print_entry(boxname)


@cmd_list.command("deployments")
@pass_appctx
def cmd_list_deployments(ctx: AppCtx) -> None:
    """ List existing deployments. """
    logger.debug("list deployments")
    deployments_lst = _list_deployments()
    if len(deployments_lst) == 0:
        click.secho("No deployments found", fg="cyan")
        return

    deployments_path = _find_deployments_path()
    assert deployments_path.exists()

    deployments: List[DeploymentModel] = []
    for entry in deployments_lst:
        deployment = deployments_path.joinpath(entry)
        assert deployment.exists()

        created_on = ""
        createdon_path = deployment.joinpath("created_on")
        if createdon_path.exists():
            created_on = createdon_path.read_text()

        deployments.append(
            DeploymentModel(name=entry, created_on=created_on)
        )

    json_lst: List[Dict[str, Any]] = []
    for deployment in deployments:

        if ctx.json:
            json_lst.append(
                {"name": deployment.name, "created_on": deployment.created_on}
            )
            continue

        createdon_str = ""
        if deployment.created_on:
            created_on = dt.fromisoformat(deployment.created_on)
            createdon_str = f"(created on: {deployment.created_on})"

        print("{} {} {}".format(
            click.style("*", fg="cyan"),
            click.style(deployment.name, fg="white", bold=True),
            click.style(createdon_str, fg="white")
        ))
    if ctx.json:
        print(json.dumps(json_lst))


def _parse_vagrant(raw: str) -> Dict[str, List[Tuple[str, str]]]:

    result: Dict[str, List[Tuple[str, str]]] = {}
    lines = raw.splitlines()

    for line in lines:
        fields = line.split(",")
        entry: Tuple[str, str] = (fields[1], fields[3])
        state: str = fields[2]
        if state not in result:
            result[state] = []
        result[state].append(entry)

    return result


def _get_vagrant_status() -> Dict[str, List[Tuple[str, str]]]:
    proc = subprocess.run(
        shlex.split("vagrant status --machine-readable"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout = proc.stdout.decode("utf-8")
    stderr = proc.stderr.decode("utf-8")
    if proc.returncode != 0:
        logger.error(f"error getting vagrant status: {stderr}")
        raise BaseError("unable to obtain vagrant status")

    return _parse_vagrant(stdout)


def _check_vagrant_state(statenames: List[str]) -> bool:

    try:
        metadata: Dict[str, List[Tuple[str, str]]] = _get_vagrant_status()
    except BaseError as e:
        logger.error(f"Error obtaining Vagrant status: {e.message}")
        raise e

    if "state" not in metadata:
        logger.error("Unable to find Vagrant machine's state")
        raise BaseError("unable to find Vagrant machine's state")

    num_at_state: int = 0
    num_nodes: int = 0

    for _, state in metadata["state"]:
        num_nodes += 1
        if state in statenames:
            num_at_state += 1

    assert num_nodes > 0
    return num_at_state > 0


#
# start, stop
#

def _vagrant_enter_deployment(name: str) -> None:

    # may raise DeploymentNotFound
    deployment = _get_deployment_path(name)

    try:
        os.chdir(deployment)
    except Exception as e:
        logger.error(f"unable to change directories: {str(e)}")
        raise EnterDeploymentError(str(e))

    vagrantfile = deployment.joinpath("Vagrantfile")
    if not vagrantfile.exists():
        logger.error(f"unable to find Vagrantfile at {vagrantfile}")
        raise DeploymentNotFinishedError()


def _cmd_try_vagrant_deployment(name: str) -> None:

    error: int = 0
    try:
        _vagrant_enter_deployment(name)
    except DeploymentNotFoundError:
        click.secho(f"Deployment '{name}' not found", fg="red")
        error = errno.ENOENT
    except DeploymentNotFinishedError:
        click.secho(f"Deployment '{name}' wasn't finished. Should recreate.")
        error = errno.EINVAL
    except FileNotFoundError:
        click.secho("Couldn't find Deployment's directory")
        error = errno.ENOENT
    except PermissionError:
        click.secho(f"No permissions to use Deployment '{name}'")
        error = errno.EPERM

    if error != 0:
        sys.exit(error)


@app.command("start")
@click.argument("name", required=True, type=str)
@pass_appctx
def cmd_start(ctx: AppCtx, name: str) -> None:

    _cmd_try_vagrant_deployment(name)

    try:
        running: bool = _check_vagrant_state(["running", "preparing"])
    except BaseError as e:
        click.secho(f"Something went wrong: {e.message}", fg="red")
        sys.exit(errno.EINVAL)

    if running:
        click.secho("Deployment already running", fg="yellow")
        return

    proc = subprocess.run(
        shlex.split("vagrant up"),
        stderr=subprocess.PIPE
    )

    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8")
        logger.error(f"unable to start vagrant machines: {stderr}")
        click.secho("Unable to start deployment", fg="red")
        sys.exit(1)

    click.secho("Deployment started.")


@app.command("stop")
@click.argument("name", required=True, type=str)
@pass_appctx
def cmd_stop(ctx: AppCtx, name: str) -> None:

    _cmd_try_vagrant_deployment(name)

    try:
        stopped: bool = _check_vagrant_state(["shutoff", "not_created"])
    except BaseError as e:
        click.secho(f"Something went wrong: {e.message}", fg="red")
        sys.exit(errno.EINVAL)

    if stopped:
        click.secho("Deployment already stopped.", fg="green")
        return

    proc = subprocess.run(
        shlex.split("vagrant destroy"),
        stderr=subprocess.PIPE
    )

    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8")
        logger.error(f"Unable to stop vagrant machines: {stderr}")
        click.secho("Unable to stop deployment", fg="red")
        sys.exit(1)

    click.secho("Deployment stopped.", fg="green")


if __name__ == "__main__":
    app()
