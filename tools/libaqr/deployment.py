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

from __future__ import annotations
import os
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime as dt
import random
import shutil

from pydantic import BaseModel, Field

import libaqr.vagrant as vagrant
from libaqr.errors import (
    AqrError,
    BoxDoesNotExistError,
    DeploymentExistsError,
    DeploymentNotFinishedError,
    DeploymentNotFoundError,
    DeploymentNotRunningError,
    DeploymentRunningError
)
from libaqr.misc import list_boxes


logger: logging.Logger = logging.getLogger("aquarium")


class DeploymentModel(BaseModel):
    name: str = Field(..., description="Name of Deployment")
    box: str = Field(..., description="Deployment's Box's Name")
    created_on: dt = Field(..., description="Date of creation")
    num_disks: Optional[int] = Field(None, description="Number of disks")
    num_nics: Optional[int] = Field(None, description="Number of NICs")
    num_nodes: Optional[int] = Field(None, description="Number of Nodes")


class Deployment:

    _meta: DeploymentModel
    _path: Path

    def __init__(self, path: Path, meta: DeploymentModel):
        self._path = path
        self._meta = meta

    @property
    def name(self) -> str:
        return self._meta.name

    @property
    def box(self) -> str:
        return self._meta.box

    @property
    def created_on(self) -> dt:
        return self._meta.created_on

    @property
    def meta(self) -> DeploymentModel:
        return self._meta

    def __repr__(self) -> str:
        return str(self._meta)

    @classmethod
    def create(
        cls,
        name: str,
        box: str,
        num_nodes: int,
        num_disks: int,
        num_nics: int,
        deployments_path: Path,
        mount_path: Optional[Path] = None
    ) -> Deployment:

        if not deployments_path.exists():
            raise FileNotFoundError(deployments_path)

        path = deployments_path.joinpath(name)
        if path.exists():
            raise DeploymentExistsError()

        if box not in list_boxes():
            raise BoxDoesNotExistError(box)

        try:
            logger.debug(f"creating deployment '{name}'")
            path.mkdir()
        except Exception as e:
            logger.error(f"unable to create deployment: {str(e)}")
            raise AqrError(f"error creating deployment '{name}': {str(e)}")

        vagrantfile_text = _gen_vagrantfile(
            box, mount_path,
            num_nodes, num_disks, num_nics
        )
        vagrantfile = path.joinpath("Vagrantfile")
        logger.debug(f"writing Vagrantfile at '{vagrantfile}'")
        vagrantfile.write_text(vagrantfile_text)

        meta = DeploymentModel(
            name=name,
            box=box,
            created_on=dt.now(),
            num_disks=num_disks,
            num_nics=num_nics,
            num_nodes=num_nodes
        )
        metafile = path.joinpath("meta.json")
        metafile.write_text(meta.json())

        return Deployment(path, meta)

    @classmethod
    def load(cls, deployments_path: Path, name: str) -> Deployment:
        """ Load deployment from disk """
        if not deployments_path.exists():
            raise FileNotFoundError(deployments_path)

        path = deployments_path.joinpath(name)
        if not path.exists():
            raise DeploymentNotFoundError(name)

        metafile = path.joinpath("meta.json")
        if not metafile.exists():
            raise DeploymentNotFinishedError(name)

        meta = DeploymentModel.parse_file(metafile)
        return Deployment(path, meta)

    def start(self, conservative: bool) -> None:
        """ Start deployment """
        try:
            with vagrant.deployment(self._path) as deployment:
                if deployment.running or deployment.preparing:
                    raise DeploymentRunningError()
                deployment.start(conservative=conservative)
        except AqrError as e:
            raise e

    def stop(self) -> None:
        """ Stop deployment """
        try:
            with vagrant.deployment(self._path) as deployment:
                if deployment.shutoff or deployment.notcreated:
                    return  # nothing to do.
                deployment.stop()
        except AqrError as e:
            raise e

    def shell(self, node: Optional[str], cmd: Optional[str]) -> int:
        """ Open shell into the deployment """
        try:
            with vagrant.deployment(self._path) as deployment:
                if not deployment.running:
                    raise DeploymentNotRunningError()
                return deployment.shell(node, cmd)
        except AqrError as e:
            raise e

    def remove(self) -> None:
        """ Remove the deployment """
        with vagrant.deployment(self._path) as deployment:
            if deployment.running or deployment.preparing:
                raise DeploymentRunningError()
        shutil.rmtree(self._path)

    def status(self) -> List[Tuple[str, str]]:
        """ Obtain status for each node """
        status: List[Tuple[str, str]] = []
        with vagrant.deployment(self._path) as deployment:
            nodes_status = deployment.nodes_status
            for node_name, node_state in nodes_status:
                state = "unknown"
                if node_state == vagrant.VagrantStateEnum.RUNNING:
                    state = "running"
                elif node_state == vagrant.VagrantStateEnum.PREPARING:
                    state = "preparing"
                elif node_state == vagrant.VagrantStateEnum.SHUTOFF:
                    state = "shutoff"
                elif node_state == vagrant.VagrantStateEnum.NOT_CREATED:
                    state = "not created"
                status.append((node_name, state))
        return status


def _gen_vagrantfile(
    boxname: str,
    rootdir: Optional[Path],
    nodes: int,
    disks: int,
    nics: int
) -> str:

    logger.debug(
        f"generate template: nodes={nodes}, disks={disks}, nics={nics}"
    )

    without_nfs_str: str = "true" if not rootdir else "false"
    rootdir = rootdir if rootdir else Path(".")

    template: str = \
        f"""
# -*- mode: ruby -*-
# vim: set ft=ruby

Vagrant.configure("2") do |config|
    config.vm.box = "{boxname}"
    config.vm.synced_folder ".", "/vagrant", disabled: true
    config.vm.synced_folder "{rootdir}", "/srv/aquarium", type: "nfs", nfs_udp: false, disabled: {without_nfs_str}
    config.vm.guest = "suse"

        """

    host_port = 1337
    for nid in range(1, nodes+1):

        node_networks: str = ""
        for _ in range(0, nics-1):
            node_networks += \
                """
        node.vm.network :private_network, :type => "dhcp"
                """

        node_storage: str = ""
        for _ in range(disks):
            serial = "".join(random.choice("0123456789") for _ in range(8))
            node_storage += \
                f"""
            lv.storage :file, size: "8G", type: "qcow2", serial: "{serial}"
                """

        is_primary_str = "true" if nid == 1 else "false"
        node_str: str = \
            f"""
    config.vm.define :"node{nid}", primary: {is_primary_str} do |node|
        node.vm.hostname = "node{nid}"
        node.vm.network "forwarded_port", guest: 1337, host: {host_port}, host_ip: "*"
        {node_networks}

        node.vm.provider "libvirt" do |lv|
            lv.memory = 4096
            lv.cpus = 1
            {node_storage}
        end
    end
            """

        template += node_str
        host_port += 1

    template += \
        """
end
        """

    return template


def get_deployments(path: Path) -> Dict[str, Deployment]:
    results: Dict[str, Deployment] = {}
    for entry in next(os.walk(path))[1]:
        try:
            deployment = Deployment.load(path, entry)
            results[entry] = deployment
        except DeploymentNotFinishedError:
            logger.debug(f"deployment '{entry}' not finished")
            continue
        except Exception as e:
            raise e
    return results
