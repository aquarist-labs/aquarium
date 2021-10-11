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

import sys
import errno
import json
from typing import Any, Dict, List, Optional, Tuple
import click
import logging
from click.decorators import make_pass_decorator
from pathlib import Path

from libaqua.images import Image
from libaqua.deployment import Deployment, VagrantDeployment, DeploymentModel, get_deployments
from libaqua.errors import (
    AqrError,
    BoxAlreadyExistsError,
    BuildsPathNotFoundError,
    DeploymentNodeDoesNotExistError,
    DeploymentNodeNotRunningError,
    DeploymentNotFinishedError,
    DeploymentNotFoundError,
    DeploymentNotRunningError,
    DeploymentPathNotFoundError,
    DeploymentRunningError,
    ImageNotFoundError,
    RootNotFoundError,
    VagrantError
)
from libaqua.misc import (
    find_builds_path,
    find_deployments_path,
    find_root
)
from libaqua.vagrant import Vagrant

logger: logging.Logger = None

from functools import partial
click.option = partial(click.option, show_default=True)


class AppCtx:

    _json_output: bool
    _root_path: Path
    _builds_path: Optional[Path]
    _deployments_path: Optional[Path]
    _deployments: Optional[Dict[str, Deployment]]

    def __init__(
        self,
        json_output: bool,
        root_path: Path
    ):
        self._json_output = json_output
        self._root_path = root_path

        self._builds_path = None
        self._deployments_path = None
        self._deployments = None

    @property
    def json(self) -> bool:
        return self._json_output

    @property
    def root_path(self) -> Path:
        return self._root_path

    @property
    def builds_path(self) -> Path:
        if not self._builds_path:
            # propagate exception to caller
            self._builds_path = find_builds_path()
        return self._builds_path

    @property
    def deployments_path(self) -> Path:
        if not self._deployments_path:
            # propagate exception to caller
            self._deployments_path = find_deployments_path()
        return self._deployments_path

    @property
    def deployments(self) -> Dict[str, Deployment]:
        if not self._deployments:
            # propagate exceptions to caller
            self._deployments = get_deployments(self.deployments_path)
        return self._deployments


pass_appctx = make_pass_decorator(AppCtx)


@click.group()
@click.option("-d", "--debug", flag_value=True)
@click.option("-t", "--trace", flag_value=True)
@click.option("--json", flag_value=True)
@click.pass_context
def app(ctx: click.Context, debug: bool, json: bool, trace: bool) -> None:

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif trace:
        format_str = '%(asctime)s %(levelname)s:%(module)s:%(funcName)s:%(lineno)s:%(message)s'
        logging.basicConfig(level=logging.DEBUG, format=format_str)
    else:
        logging.basicConfig(level=logging.INFO)

    global logger
    logger = logging.getLogger("aquarium")

    rootpath: Optional[Path] = None

    try:
        rootpath = find_root()
    except RootNotFoundError:
        click.secho("Unable to find git repository's root", fg="red")
        sys.exit(errno.ENOENT)

    logger.debug(f"app => debug: {debug}, ctx: {ctx}")
    ctx.obj = AppCtx(
        json_output=json,
        root_path=rootpath
    )


def _get_deployment(ctx: AppCtx, name: str) -> Deployment:
    deployment: Optional[Deployment] = None
    try:
        all_deployments = ctx.deployments
        if name not in all_deployments:
            raise DeploymentNotFoundError()
        deployment = all_deployments[name]
    except DeploymentPathNotFoundError:
        click.secho("Unable to find deployments path", fg="red")
        sys.exit(errno.ENOENT)
    except DeploymentNotFoundError:
        click.secho(f"Deployment {name} not found", fg="red")
        sys.exit(errno.ENOENT)
    except DeploymentNotFinishedError:
        click.secho(
            f"Deployment {name} wasn't finished. Should recreate.",
            fg="red"
        )
        sys.exit(errno.EINVAL)
    except Exception as e:
        click.secho(f"Unknown error: {str(e)}", fg="red")
        sys.exit(errno.EINVAL)
    return deployment


#
# create and remove setups
#
@app.command("create")
@click.option("-b", "--box", type=str, required=False,
              help="Deployment box, run 'box list' for all available boxes")
@click.option("-c", "--connect", type=str, required=False,
              help="Libvirt connect URI, for example 'qemu+ssh://localhost/system'",
              default='qemu:///system')
@click.option("-i", "--image", type=str, required=False,
              help="Deployment image, run 'image list' for all available images")
@click.option("-f", "--force", flag_value=True,
              help="Override corresponding box if needed")
@click.option("-t", "--deployment-type", type=str, default='vagrant',
              help="Deployment type: vagrant, libvirt")
@click.option("--cdrom", type=str, required=False,
              help="Path to iso image to be used for the first boot")
@click.option("--disk-size", required=False, type=int, default=10, show_default=True,
              help="Disk size, in GB")
@click.option("--num-nodes", required=False, type=int, default=2, show_default=True,
              help="Number of nodes in deployment")
@click.option("--num-disks", required=False, type=int, default=4, show_default=True,
              help="Number of disks per node")
@click.option("--num-nics", required=False, type=int, default=1, show_default=True,
              help="Number of networks in deployment")
@click.argument("name", required=True, type=str)
@pass_appctx
def cmd_create(
    ctx: AppCtx,
    name: str,
    box: Optional[str],
    connect: Optional[str],
    image: Optional[str],
    force: bool,
    deployment_type: str,
    cdrom: str,
    disk_size: Optional[int],
    num_nodes: Optional[int],
    num_disks: Optional[int],
    num_nics: Optional[int]
) -> None:
    """
    Create a new deployment with given name and required type.

    If deployment with the NAME exists, report about error and quit.

    For vagrant deployments any of --box or --image options could be used.
    When none of the --box or --image options provided, it will try to
    find box with default name (aquarium) or the same name as the deployment.
    If there is no suitable box, then it can be created using image with
    the default name or same name as the deployment correspondingly.
    If no image found in turn, fail with error message.
    Fails with error message if both --box and --image provided.

    For libvirt deployments --connect options is used.

    """
    logger.debug(f"create: ctx = {ctx}, name: {name}, box: {box}, img: {image}")

    if deployment_type == 'vagrant':
        # create vagrant deployment
        avail_boxes = Vagrant.box_list()
        if box and image:
            click.secho(
                "Please provide only one of '--box' or '--image'", fg="red")
            sys.exit(errno.EINVAL)
        if box:
            avail_box_iter = (name for name, _ in avail_boxes)
            if box not in avail_box_iter:
                click.secho(f"Unable to find box '{box}'", fg="red")
                sys.exit(errno.EINVAL)

        # if given box name, reuse existing box
        # if image name requested, create corresponding vagrant box and use it for deployment
        # (removing existing vagrant box).
        # if non of box or image requested, we try and find box or image

        elif not box and not image:
            pass

    elif deployment_type == 'libvirt':
        from libaqua.deployment import LibvirtDeployment
        # create libvirt deployment
        mount_path = find_root()
        LibvirtDeployment.create(
            name, num_nodes, num_disks, num_nics, disk_size,
            ctx.deployments_path, mount_path,
            uri=connect, cdrom=cdrom,
        )
        return
    else:
        click.secho(f"Unsupportable deployment type: '{deployment_type}'", fg="red")
        sys.exit(errno.ENOENT)

    avail_images: Optional[List[str]] = None
    avail_deployments: List[Deployment] = []
    try:
        avail_images = Image.list(find_builds_path())
        avail_deployments = [v for v in ctx.deployments.values()]
    except RootNotFoundError:
        click.secho("Unable to find git repository's root dir")
        sys.exit(errno.ENOENT)
    except Exception:
        pass

    if any([True for d in avail_deployments if d.name == name]):
        click.secho(f"Deployment '{name}' already exists", fg="red")
        sys.exit(errno.EEXIST)

    """
    User did not assign box or image
    1) search for existing default aquarium box and provider type, 
       then flag it aquarium_box_exist to True
    2) look up available image name and provider type, 
       then flag it aquarium_image_exist to True
    3) if neither exist, then error out exit 
    """
    if not box and not image:
        click.secho(f"Using default 'aquarium' as box name and image name", fg="green")
        aquarium_box_exist = False
        aquarium_image_exist = False
        # search for box with name 'aquarium' or deployment name
        for box_name, provider_name in avail_boxes:
            if box_name == "aquarium" or box_name == name:
                aquarium_box_exist = True
                box = box_name
                provider = provider_name
        # if any box found then ensure there is an image with corresponding name
        # and provider, otherwise find image with default name 'aquarium'
        # or deployment name
        for img_obj in avail_images:
            if aquarium_box_exist:
                if img_obj.name == box and img_obj.provider == provider:
                    aquarium_image_exist = True
            elif img_obj.name == "aquarium" or img_obj.name == name and img_obj.provider == provider:
                aquarium_image_exist = True
                image = img_obj.name
                provider = img_obj.provider

        # if neither box or image cannot be found then exit with error, otherwise
        # report about our findings.
        if aquarium_box_exist:
            click.secho(f"Box '{box}' exist with Provider '{provider}' is availble", fg="green")
        elif aquarium_image_exist:
            click.secho(f"Image '{image}' exist with Provider '{provider}' is availble", fg="green")
        else:
            click.secho("Unable to find default box or default image 'aquarium'", fg="red")
            sys.exit(errno.ENOENT)

    """
    Either User assign the image name or we get it from listing existing image
    1) check if user assign image still exist
    2) if image name is box name with force flag, remove the box
    3) create box with image name, if image already in box list with no force flag, reuse
    """
    if not box and image:
        click.secho(f"Using image '{image}' to create box and deployment", fg="green")

        if image not in [i.name for i in avail_images]:
            click.secho(f"Image '{image}' not found", fg="red")
            sys.exit(errno.ENOENT)

        if image in [image_name for image_name, _ in avail_boxes] and force:
            # remove existing box first
            try:
                Vagrant.box_remove(image)
            except AqrError as e:
                logger.error(
                    f"Unable to remove existing box '{image}': {e.message}"
                )
                sys.exit(1)

        if not avail_images:
            click.secho("No images found", fg="red")
            sys.exit(errno.ENOENT)

        try:
            click.secho(f"Importing image '{image}' as Vagrant box", fg="cyan")
            builds_path = ctx.builds_path
            # add vagrant box with image, should result with the same name
            Image.add(builds_path, image)
            avail_boxes = Vagrant.box_list()
            box = image
            click.secho(
                f"Imported image '{image}' as Vagrant box",
                fg="green"
            )
        except VagrantError as e:
            click.secho(f"Error importing image '{image}': {e.message}")
            sys.exit(e.errno)
        except BoxAlreadyExistsError:
            click.secho("Box already exists, reusing.", fg="green")
            box = image
        except ImageNotFoundError as e:
            click.secho(f"Error importing image '{image}': {e.message}")
            sys.exit(e.errno)
        except BuildsPathNotFoundError:
            click.secho("Unable to find builds path", fg="red")
            sys.exit(errno.ENOENT)
        for image_name, provider_name in avail_boxes:
            if image_name == image:
                box = image
                provider = provider_name
        click.secho(f"Imported image: '{box}' as Vagrant box Provider: {provider}", fg="green")
    elif box and image:
        click.secho("Please provide only one of '--box' or '--image'", fg="red")
        sys.exit(errno.EINVAL)

    assert box is not None
    box_exist = False
    for box_name, provider_name in avail_boxes:
        if box_name == box:
            provider = provider_name
            box_exist = True
    if box_exist:
        click.secho(f"Using box '{box}' provider '{provider}'", fg="green")
    else:
        click.secho(f"Unable to find box '{box}'", fg="red")
        return

    # mount path should point to the current repo root directory
    mount_path = find_root()
    try:
        VagrantDeployment.create(
            name, box, provider, num_nodes, num_disks, num_nics, disk_size,
            ctx.deployments_path, mount_path
        )
    except DeploymentPathNotFoundError:
        click.secho("Unable to find deployments path", fg="red")
        sys.exit(errno.ENOENT)
    except Exception as e:
        click.secho(
            f"Error creating deployment '{name}' from box '{box}': {str(e)}",
            fg="red"
        )
        raise e
    click.secho("success!", fg="green")


@app.command("remove")
@click.argument("name", required=True, type=str)
@pass_appctx
def cmd_remove(ctx: AppCtx, name: str) -> None:
    """
    Remove a deployment; doesn't remove the deployment's box
    """
    logger.debug(f"remove => name: {name}, ctx: {ctx}")

    deployment: Deployment = _get_deployment(ctx, name)
    try:
        deployment.remove()
    except DeploymentRunningError:
        click.secho("Please stop the deployment before removing", fg="yellow")
        sys.exit(errno.EBUSY)
    except AqrError as e:
        click.secho(f"Unkown error: {e.message}")
        raise(e)
        sys.exit(e.errno)

    click.secho("Removed.", fg="green")


def print_entry(name: str) -> None:
    """ Print an entry in the format '* NAME', with pretty colors """
    print("{} {}".format(
        click.style("*", fg="cyan"),
        click.style(name, fg="white", bold=True)
    ))


def print_json(what: Any) -> None:
    print(json.dumps(what))


@app.command("start")
@click.argument("name", required=True, type=str)
@click.option("--conservative", flag_value=True)
@pass_appctx
def cmd_start(ctx: AppCtx, name: str, conservative: bool) -> None:
    """
    Start a deployment
    """
    deployment: Deployment = _get_deployment(ctx, name)
    assert deployment
    try:
        deployment.start(conservative)
    except DeploymentRunningError:
        click.secho("Deployment already running", fg="yellow")
        return
    except AqrError as e:
        click.secho(f"Error: {e.message}", fg="red")
        sys.exit(e.errno)
    except Exception as e:
        click.secho(f"Unknown error: {str(e)}", fg="red")
        sys.exit(errno.EINVAL)

    click.secho(f"Deployment '{name}' started", fg="green")
    return


@app.command("stop")
@click.option("-f", "--force", flag_value=True)
@click.argument("name", required=True, type=str)
@pass_appctx
def cmd_stop(ctx: AppCtx, name: str, force: bool) -> None:
    """
    Stop deployment; destroys running machines
    """
    deployment: Deployment = _get_deployment(ctx, name)
    assert deployment

    try:
        deployment.stop(force=force)
    except AqrError as e:
        click.secho(f"Error: {e.message}", fg="red")
        sys.exit(e.errno)
    except Exception as e:
        click.secho(f"Unknown error: {str(e)}", fg="red")
        sys.exit(errno.EINVAL)

    click.secho("Deployment stopped.", fg="green")


@app.command("shell")
@click.argument("name", required=True, type=str)
@click.option("-n", "--node", required=False, type=str)
@click.option("-c", "--command", required=False, type=str)
@pass_appctx
def cmd_shell(
    ctx: AppCtx,
    name: str,
    node: Optional[str],
    command: Optional[str]
) -> None:
    """
    Obtain a shell for a deployment; can specify node
    """
    deployment: Deployment = _get_deployment(ctx, name)
    assert deployment

    try:
        sys.exit(deployment.shell(node, command))
    except DeploymentNotRunningError:
        click.secho("Deployment not running", fg="red")
        sys.exit(errno.EAGAIN)
    except DeploymentNodeDoesNotExistError:
        click.secho(f"Node '{node}' does not exist", fg="red")
        sys.exit(errno.ENOENT)
    except DeploymentNodeNotRunningError:
        click.secho(f"Node '{node}' not running", fg="red")
        sys.exit(errno.EAGAIN)


@app.command("status")
@click.argument("name", required=False, type=str)
@pass_appctx
def cmd_status(ctx: AppCtx, name: Optional[str]) -> None:
    """
    Obtain status of existing deployments
    """

    deployments: Dict[str, Deployment] = {}
    try:
        deployments = ctx.deployments
    except Exception:
        pass

    if name:
        if name not in deployments:
            click.secho(f"Unknown deployment '{name}'", fg="red")
            sys.exit(errno.ENOENT)
        deployment = deployments[name]
        deployments = {name: deployment}

    for name, deployment in deployments.items():
        hdr = chr(0x25CF)
        click.secho("{} {}".format(
            click.style(hdr, fg="cyan", bold=True),
            click.style(f"{name}", fg="white", bold=True)
        ))

        status: List[Tuple[str, str]] = deployment.status()
        while len(status) > 0:
            entry: Tuple[str, str] = status.pop(0)
            boxline = chr(0x251C)
            if len(status) == 0:
                boxline = chr(0x2514)

            node, node_state = entry
            color = "yellow"
            if node_state == "running":
                color = "green"
            elif node_state == "not created":
                color = "red"
            node_state = " ".join(node_state.split("_"))
            click.secho("{} {} {}".format(
                click.style(boxline, fg="cyan", bold=True),
                click.style(f"{node}:", fg="white"),
                click.style(node_state, fg=color)
            ))


@app.command("list")
@click.option("-v", "--verbose", flag_value=True)
@pass_appctx
def cmd_list(ctx: AppCtx, verbose: bool) -> None:
    """
    List existing deployments
    """
    logger.debug("list deployments")
    deployments: List[Deployment] = []

    try:
        deployments = [v for v in ctx.deployments.values()]
    except Exception:
        pass

    if len(deployments) == 0:
        click.secho("No deployments found", fg="cyan")
        return


    if ctx.json:
        json_list = [json.loads(_.meta.json()) for _ in deployments]
        print(json.dumps(json_list))
        return

    if not verbose:
        for _ in deployments:
            print(_.name)
        return

    for deployment in deployments:

        header = chr(0x25cf)
        click.secho("{} {}".format(
            click.style(header, fg="cyan", bold=True),
            click.style(f"{deployment.name}", fg="white", bold=True)
        ))

        def _print(prefix: str, what: str, value: str) -> None:
            click.secho("{} {}: {}".format(
                click.style(prefix, fg="cyan", bold=True),
                click.style(what, fg="white", bold=True),
                click.style(value, fg="white")
            ))

        treeline = chr(0x251c)
        treeend = chr(0x2514)

        model = deployment.meta.model
        if isinstance(deployment, VagrantDeployment):
            if model:
                _print(treeline, "model", model)
            boxname = deployment.box if deployment.box else "unknown"
            _print(treeline, "created on", str(deployment.created_on))
            _print(treeend, "box", boxname)
        else:
            if model:
                _print(treeend, "model", model)


#
# box-related commands
#
@app.group("box")
def cmd_box() -> None:
    """
    Box related commands
    """
    logger.debug("box")
    pass


@cmd_box.command("list")
@click.option("-v", "--verbose", flag_value=True)
@pass_appctx
def cmd_box_list(ctx: AppCtx, verbose: bool) -> None:
    logger.debug("list boxes")
    boxes: List[Tuple[str, str]] = Vagrant().box_list()
    deployments: List[Deployment] = []
    try:
        deployments = [v for v in ctx.deployments.values()]
    except Exception:
        pass

    deployment_per_box: Dict[str, List[DeploymentModel]] = {}
    logger.debug(f'Vagrant boxes: {boxes}')
    logger.debug(f'Deployments: {deployments}')

    for deployment in deployments:
        box = deployment.box
        if box and box in (name for (name, _) in boxes):
            if box not in deployment_per_box:
                deployment_per_box[box] = []
            deployment_per_box[box].append(deployment.meta)

    if len(boxes) == 0:
        click.secho("No boxes found", fg="cyan")
        return

    if ctx.json:
        print_json(boxes)
        return

    headerchr = chr(0x25cf)
    for boxname, provider in boxes:
        num_deployments = len(deployment_per_box.get(boxname, []))
        click.secho("{} {} ({}) ({} deployments)".format(
            click.style(headerchr, fg="cyan", bold=True),
            click.style(boxname, fg="white", bold=True),
            click.style(provider, fg="white", bold=False),
            num_deployments
        ))

        if verbose and num_deployments > 0:
            lst = deployment_per_box[boxname]
            while len(lst) > 0:
                dep = lst.pop(0)
                prefix = chr(0x251c) if len(lst) > 0 else chr(0x2514)
                click.secho("{} {}".format(
                    click.style(prefix, fg="cyan", bold=True),
                    click.style(dep.name, fg="white")
                ))


#
# image related commands
#
@app.group("image")
def cmd_images() -> None:
    """
    Image related commands
    """
    logger.debug("image")
    pass


@cmd_images.command("list")
@pass_appctx
def cmd_images_list(ctx: AppCtx) -> None:
    logger.debug("list images")

    buildspath = find_builds_path()
    images = Image.list(buildspath)

    if len(images) == 0:
        click.secho("No images found", fg="cyan")
        return

    lst: List[Dict[str, str]] = []
    for entry in images:
        lst.append({
            "name": entry.name,
            "path": str(entry.path),
            "provider": entry.provider
        })
        if not ctx.json:
            ext = str(entry.path).rsplit('.')[-1]
            print("{} {} ({}, {})".format(
                click.style("*", fg="cyan"),
                click.style(entry.name, fg="white", bold=True),
                click.style(ext, fg="white"),
                click.style(entry.provider, fg="white")
            ))
    if ctx.json:
        print(json.dumps(lst))

@cmd_images.command("build")
@click.option("-t", "--image-type", type=str, required=False, default="vagrant",
              help="Specify image type "
                   "(vagrant, vagrant-libvirt, vagrant-virtualbox, self-install, live-iso)")
@click.option("-c", "--clean", flag_value=False,
              help="Cleanup existing build directory before building")
@pass_appctx
def cmd_images_build(ctx: AppCtx,
                     image_type: str,
                     clean: bool,
                     ) -> None:
    logger.debug("build images")

