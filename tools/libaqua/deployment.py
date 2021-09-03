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
import sys
import json

from pydantic import BaseModel, Field


import libaqua.vagrant as vagrant
from libaqua.errors import (
    AqrError,
    BoxDoesNotExistError,
    DeploymentExistsError,
    DeploymentNotFinishedError,
    DeploymentNotFoundError,
    DeploymentNotRunningError,
    DeploymentRunningError
)

logger: logging.Logger = logging.getLogger("aquarium")


class DeploymentModel(BaseModel):
    model: Optional[str] = Field(None, description="Type of Deployment")
    name: str = Field(..., description="Name of Deployment")
    created_on: dt = Field(..., description="Date of creation")
    num_disks: Optional[int] = Field(None, description="Number of disks")
    num_nics: Optional[int] = Field(None, description="Number of NICs")
    num_nodes: Optional[int] = Field(None, description="Number of Nodes")

class VagrantDeploymentModel(DeploymentModel):
    model: str = Field('Vagrant')
    box: str = Field(..., description="Deployment's Box's Name")


class Deployment:

    _meta: DeploymentModel
    _path: Path

    def __init__(self, path: Path, meta: DeploymentModel):
        logger.debug('init class')
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
    def get_models(cls):
        models = (_name for (_name, _class) in
                                    sys.modules[__name__].__dict__.items()
                    if _name.endswith('Model')
                        and issubclass(_class, DeploymentModel)
                        and _name != 'DeploymentModel')
        return models

    @classmethod
    def get_classes(cls):
        classes = (_name for (_name, _class) in
                                    sys.modules[__name__].__dict__.items()
                    if _name.endswith('Deployment')
                        and issubclass(_class, Deployment))
        return classes

    @classmethod
    def _parse_obj(cls, meta):

        model = meta.get('model')
        if model:
            model_name = f"{meta.get('model')}DeploymentModel"

            if model_name in cls.get_models():
                model_cls = sys.modules[__name__].__dict__[model_name]
                return model_cls.parse_obj(meta)
            else:
                raise AqrError(f'Unknown deployment model {model_name}')
        else:
            logger.warning(f'Cannot determine model')
            return DeploymentModel.parse_obj(meta)


    def start(self, conservative: bool) -> None:
        pass

    def stop(self, force: bool = False) -> None:
        pass

    def save(self) -> None:
        if not self._path.exists():
            raise DeploymentNotFoundError(f"{self._meta} {self._path} 'name'")

        metafile = self._path.joinpath("meta.json")
        metafile.write_text(self._meta.json())

    @classmethod
    def _create(cls, name: str, deployments_path: Path) -> None:
        path = deployments_path.joinpath(name)
        if path.exists():
            logger.debug(f"deployment path exists: '{path}'")
            raise DeploymentExistsError()
        try:
            logger.debug(f"creating deployment '{name}'")
            path.mkdir(parents=True)
        except Exception as e:
            logger.error(f"unable to create deployment: {str(e)}")
            raise AqrError(f"error creating deployment '{name}': {str(e)}")

        return path

    @classmethod
    def create(
        cls,
        name: str,
        box: str,
        provider: str,
        num_nodes: int,
        num_disks: int,
        num_nics: int,
        deployments_path: Path,
        mount_path: Optional[Path] = None
    ) -> Deployment:

        if (box, provider) not in vagrant.Vagrant.box_list():
            logger.debug(f"boxlist: '{vagrant.Vagrant.box_list()}'")
            raise BoxDoesNotExistError(box, provider)

        path = cls._create(name=name, deployments_path=deployments_path)

        vagrantfile_text = _gen_vagrantfile(
            box, provider, mount_path,
            num_nodes, num_disks, num_nics
        )
        vagrantfile = path.joinpath("Vagrantfile")
        logger.debug(f"writing Vagrantfile at '{vagrantfile}'")
        vagrantfile.write_text(vagrantfile_text)

        meta = VagrantDeploymentModel(
            name=name,
            box=box,
            created_on=dt.now(),
            num_disks=num_disks,
            num_nics=num_nics,
            num_nodes=num_nodes
        )
        deployment = Deployment(path, meta)
        deployment.save()

        return deployment

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

        logger.debug(f'Loading meta file {metafile}')
        with open(str(metafile)) as f:
            try:
                obj = json.load(f)
                logger.debug(f'Read object: {obj}')
                meta = Deployment._parse_obj(obj)
                deployment = Deployment._meta_cls(meta)(path, meta)
                logger.debug(f'Deployment {deployment}')
                return deployment
            except Exception as e:
                logger.error(e)
                raise(e)

    @classmethod
    def _meta_cls(cls, meta):
        """
        Returns deployment class for meta.
        If corresponding class cannot be determined because of missing model,
        return Deployment.
        """
        classes = cls.get_classes()
        if hasattr(meta, 'model') and meta.model:
            class_name = f'{meta.model}Deployment'
            if class_name in classes:
                cls = sys.modules[__name__].__dict__[class_name]
                return cls
            else:
                msg = f"Class '{class_name}' does not exist"
                raise AqrError(msg)
        else:
            logger.debug(f'No model field in meta: "{meta}"')
            return Deployment



    def remove(self) -> None:
        """
        Removes the deployment if it is not running.

        :raises: DeploymentRunningError if deployment is up and running
        """
        logger.warning(f'Remove method is not implemented for '
                       f'{self.__class__.__name__} class')
        self._remove()

    def _remove(self) -> None:
        shutil.rmtree(self._path)


    def status(self) -> List[Tuple[str, str]]:
        """ Obtain status for each node """
        logger.warning(f'Nodes status is not implemented yet for '
                       f'{self.__class__.__name__} class')
        return []


def _gen_vagrantfile(
    boxname: str,
    provider: str,
    rootdir: Optional[Path],
    nodes: int,
    disks: int,
    nics: int
) -> str:

    logger.debug(
        f"generate template: nodes={nodes}, disks={disks}, nics={nics}"
    )

    without_shared_folder_str: str = "true" if not rootdir else "false"
    rootdir = rootdir if rootdir else Path(".")

    """ template for node storage, libvirt and virtualbox use different format """
    create_node_storage: str = ""
    if provider == "virtualbox":
        create_node_storage = \
                f"""
vb_config = `VBoxManage list systemproperties`.split(/\\n/).grep(/Default machine folder/).first
diskpath = vb_config.split(':', 2)[1].strip() """
        for nid in range(1, nodes+1):
            for did in range(1, disks+1):
                create_node_storage += \
                        f"""
N{nid}DISK{did} = File.join(diskpath, '{boxname}-node{nid}', 'node{nid}-disk{did}.vdi') """


    template: str = \
        f"""
# -*- mode: ruby -*-
# vim: set ft=ruby
{create_node_storage}

Vagrant.configure("2") do |config|
    config.vm.box = "{boxname}"
    config.vm.synced_folder ".", "/vagrant", disabled: true

    config.vm.provider :virtualbox do |_, override|
        override.vm.synced_folder "{rootdir}", "/srv/aquarium", type: "virtualbox", disabled: {without_shared_folder_str}
    end
    config.vm.provider :libvirt do |_, override|
        override.vm.synced_folder "{rootdir}", "/srv/aquarium", type: "nfs", nfs_udp: false, disabled: {without_shared_folder_str}
    end

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
        if provider == "virtualbox":
            node_storage += \
                    f"""
            lv.customize ['storagectl', :id, '--name', 'SATA Controller', '--portcount', '6'] """

        disk_size = '8G'
        for did in range(1, disks+1):
            if provider == "libvirt":
                serial = "".join(random.choice("0123456789") for _ in range(8))
                node_storage += \
                        f"""
            lv.storage :file, size: "{disk_size}", type: "qcow2", serial: "{serial}" """
            elif provider == "virtualbox":
                node_storage += \
                        f"""
            unless File.exist?(N{nid}DISK{did})
                lv.customize ['createhd', '--filename', N{nid}DISK{did}, '--format', 'VDI', '--size', '20000' ]
            end
            lv.customize ['storageattach', :id,  '--storagectl', 'SATA Controller', '--port', {did}, '--device', 0, '--type', 'hdd', '--medium', N{nid}DISK{did}] """


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
    logger.debug(f'Looking for deployment in {path}')
    for entry in next(os.walk(path))[1]:
        logger.debug(f'Checking {entry}')
        try:
            deployment = Deployment.load(path, entry)
            results[entry] = deployment
        except DeploymentNotFinishedError:
            logger.debug(f"deployment '{entry}' not finished")
            continue
        except Exception as e:
            logger.error(e)
            continue
            #raise e
    return results

class VagrantDeployment(Deployment):
    def shell(self, node: Optional[str], cmd: Optional[str]) -> int:
        """ Open shell into the deployment """
        try:
            with vagrant.deployment(self._path) as deployment:
                if not deployment.running:
                    raise DeploymentNotRunningError()
                return deployment.shell(node, cmd)
        except AqrError as e:
            raise e
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

    def start(self, conservative: bool) -> None:
        """ Start deployment """
        try:
            with vagrant.deployment(self._path) as deployment:
                if deployment.running or deployment.preparing:
                    raise DeploymentRunningError()
                ret, err = deployment.start(conservative=conservative)
                if not ret:
                    raise AqrError('Cannot start deployment: unknown vagrant error')
        except AqrError as e:
            raise e

    def stop(self, force: bool = False) -> None:
        """ Stop deployment """
        try:
            with vagrant.deployment(self._path) as deployment:
                if deployment.shutoff or deployment.notcreated:
                    return  # nothing to do.
                deployment.stop(force=force)
        except AqrError as e:
            raise e

    def remove(self) -> None:
        """ Remove vagrant deployment """
        with vagrant.deployment(self._path) as deployment:
            if deployment.running or deployment.preparing:
                raise DeploymentRunningError()
        self._remove()


#load other deployments and deployment models

from libaqua.libvirt import LibvirtDeployment, LibvirtDeploymentModel

