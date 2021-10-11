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

import jinja2
import json
import libvirt
import logging
import os
import sys

from datetime import datetime as dt
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Tuple
from xml.dom import minidom

from libaqua.deployment import Deployment, DeploymentModel
from libaqua.errors import (AqrError,
                            DeploymentRunningError,)

logger: logging.Logger = logging.getLogger("aquarium")

class LibvirtDeploymentModel(DeploymentModel):
    model: str = Field('Libvirt')
    uri: Optional[str] = Field(None, description="Libvirt connect URI")
    cdrom: Optional[str] = Field(None, description="Path to iso file")

class LibvirtDeployment(Deployment):

    _connect = None
    _disks = None

    @property
    def connect(self):
        if not self._connect:
            uri = self._meta.uri or 'qemu:///system'
            logger.debug(f'Connecting to libvirt via {uri}')
            conn = libvirt.open(uri)

            if conn is None:
                raise AqrError(f'Cannot connect to libvirt {uri}')
            else:
                self._connect = conn
                logger.debug(f'Connection opened: {conn}')

        return self._connect

    @classmethod
    def create(
        cls,
        name: str,
        num_nodes: int,
        num_disks: int,
        num_nics: int,
        disk_size: int,
        deployments_path: Path,
        mount_path: Optional[Path] = None,
        uri: Optional[str] = None,
        cdrom: Optional[str] = None,
    ) -> Deployment:
        path = cls._create(name=name, deployments_path=deployments_path)
        iso_path = None
        if cdrom:
            iso_path = str(Path(cdrom).absolute())
        meta = LibvirtDeploymentModel(
            name=name,
            created_on=dt.now(),
            disk_size=disk_size,
            num_disks=num_disks,
            num_nics=num_nics,
            num_nodes=num_nodes,
            uri=uri,
            cdrom=iso_path,
        )
        deployment = LibvirtDeployment(path, meta)
        deployment.save()
        deployment._create_libvirt_domains()

        return deployment

    def _network_name(self) -> str:
        return f'{self._meta.name}_network'

    def _node_name(self, index: int) -> str:
        return f'node{index}'

    def _node_vnc_port(self, index: int) -> int:
        return 5900 + index

    def node_vnc_port(self, domain_name: str) -> int:
        node_port = {
                self._libvirt_domain_name(self._node_name(_)):
                self._node_vnc_port(_)
                for _ in range(self._meta.num_nodes)}
        return node_port[domain_name]

    def _libvirt_domain_name(self, node_name: str) -> str:
        return f'{self._meta.name}_{node_name}'

    def _libvirt_node_name(self, index: int) -> str:
        return f'{self._meta.name}_{self._node_name(index)}'


    def domain_names(self) -> List[str]:
        names = [self._libvirt_domain_name(self._node_name(_))
                            for _ in range(self._meta.num_nodes)]
        return names

    @staticmethod
    def numdev(num: int) -> str:
        return str(chr(ord('a')+num))

    def _disk_source(num: int, pool: str, domain: str) -> str:
        pass

    def get_disks(self, domain_name: str, pool_name: str) -> Dict:
        if self._disks is None:
            self._disks = dict()
        d = self._disks.get(domain_name, {})
        if d:
            return d
        d = [
            dict(
                name=f'{domain_name}_drive{_}',
                dev=f'vd{self.numdev(_)}',
                alias=f'virtio-disk{_}',
                disk_format=self._disk_format,
                disk_size=self._disk_size,
                source=f'/mnt/terra/libvirt/images/{pool_name}/{domain_name}_drive{_}.img',
                    )
                    for _ in range(self._meta.num_disks)]
        self._disks[domain_name] = d
        return d

    def _disks_xml_path(self, name):
        return self._path.joinpath(f'libivirt_volume_{name}.xml')

    @property
    def _disk_format(self):
        return 'qcow2'

    @property
    def _disk_size(self):
        return self._meta.disk_size

    def _disk_xml_text(self, name, dev, alias, disk_format, disk_size, source):
        disk_capacity, capacity_unit = (disk_size, 'G')
        return (
            f'<volume><name>{name}</name>'
            f'<capacity unit="{capacity_unit}">{disk_capacity}</capacity>'
            f'<allocation>0</allocation>'
            f'<target><format type="{disk_format}"/></target>'
            f'</volume>'
            )

    def _create_libvirt_domains(self):
        names = self.domain_names()
        logger.debug(f'Creating domains: {names}')
        conn = self.connect
        doms = conn.listAllDomains()
        domain_names = [_.name() for _ in doms]
        pool_name = 'default'
        pool = conn.storagePoolLookupByName(pool_name)

        for domain_name in names:
            for di in self.get_disks(domain_name, pool_name):
                disk_xml_text = self._disk_xml_text(**di)
                self._disks_xml_path(di['name']).write_text(disk_xml_text)
                d = pool.createXML(disk_xml_text)
                di['source'] = d.key()
                logger.debug(f'{di}')
            xml_text = self.get_domain_xml(domain_name)
            logger.debug(f'Domain xml {xml_text}')
            self._domain_xml_path(domain_name).write_text(xml_text)

            logger.debug(self.get_disks(domain_name, pool_name))
            conn.defineXML(xml_text)

    def _remove_libvirt_domains(self):
        names = self.domain_names()
        logger.debug(f'Removing domains: {names}')
        conn = self.connect
        doms = conn.listAllDomains()
        domain_names = [_.name() for _ in doms]
        pool_name = 'default'
        pool = conn.storagePoolLookupByName(pool_name)
        for domain_name in names:
            if domain_name in domain_names:
                d = conn.lookupByName(domain_name)
                if d.state()[0] == libvirt.VIR_DOMAIN_RUNNING:
                    logger.warning(f'Domain {domain_name} is running, will be destroyed')
                    d.destroy()
                d.undefine()
            for di in self.get_disks(domain_name, pool_name):
                try:
                    vol = pool.storageVolLookupByName(di['name'])
                    vol.delete(flags=0)
                except:
                    pass

    def _domain_xml_path(self, domain_name):
        return self._path.joinpath(f'{domain_name}.xml')

    def _status_from_libvirt_state(self, state: int) -> str:
        _map = {
            libvirt.VIR_DOMAIN_NOSTATE: 'no',
            libvirt.VIR_DOMAIN_RUNNING: 'up',
            libvirt.VIR_DOMAIN_BLOCKED: 'block',
            libvirt.VIR_DOMAIN_PAUSED: 'pause',
            libvirt.VIR_DOMAIN_SHUTDOWN: 'down',
            libvirt.VIR_DOMAIN_SHUTOFF: 'off',
            libvirt.VIR_DOMAIN_CRASHED: 'crash',
            libvirt.VIR_DOMAIN_PMSUSPENDED: 'suspend',
            }
        if state in _map.keys():
            return _map[state]
        else:
            return 'unknown'

    def _domain_network_mac_addr_from_xml(self, xml_text):
        x = minidom.parseString(xml_text)
        networks = (_ for _ in x.getElementsByTagName('interface')
                                        if _.getAttribute('type') == 'network')
        return [_.getElementsByTagName('mac')[0].getAttribute('address') for _ in networks]

    def _domain_graphics_vnc_port_from_xml(self, xml_text):
        x = minidom.parseString(xml_text)
        vnc_graphics = (_.getAttribute('port') for _ in x.getElementsByTagName('graphics')
                                        if _.getAttribute('type') == 'vnc')
        port = next(vnc_graphics, None)
        if port == '-1':
            return None
        return port

    def status(self) -> List[Tuple[str, str]]:
        """ Obtain status for each node """
        conn = self.connect
        doms = conn.listAllDomains()
        domain_names = [_.name() for _ in doms]
        logger.debug(f'Found domains {domain_names}')
        status_map = {self._node_name(_): 'not created' for _ in range(self._meta.num_nodes)}
        node_domain_name = {self._libvirt_domain_name(self._node_name(_)): self._node_name(_)
                                for _ in range(self._meta.num_nodes)}
        net = conn.networkLookupByName('default')
        for _ in net.DHCPLeases():
            logger.debug(f'DHCP: {_}')
        for _ in doms:
            logger.debug(f'libvirt state: {_.name()} {_.state()}')
            if _.name() in node_domain_name:
                # we're looking for the first network mac address and trying to lookup ip from leases
                raw_xml = _.XMLDesc(0)
                vnc_port = self._domain_graphics_vnc_port_from_xml(raw_xml)
                logger.debug(f'Domain has openned vnc port: {vnc_port}')
                addr = self._domain_network_mac_addr_from_xml(raw_xml)[0]
                leases = (_ for _ in net.DHCPLeases() if _.get('mac') == addr)
                ipv4 = next(leases, {}).get('ipaddr', None)
                logger.debug(f'==== ADDR {_.name()} addr = {addr}, ipv4 = {ipv4}')
                if _.isActive():
                    try:
                        ifaces = _.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE, 0)
                        logger.debug(f'{_.name()}: {ifaces}')
                    except:
                        pass
                status_map[node_domain_name[_.name()]] = self._status_from_libvirt_state(_.state()[0])
        logger.debug(f'Status: {status_map}')
        return [(k,v) for (k,v) in status_map.items()]

    def start(self, conservative: bool) -> None:
        """
        Start Libvirt deployment

        Starts nodes one by one.

        Expecting to check if deployment is running or preparing and
        through DeploymentRunningError.
        raises: AqrError if deployment failed to start.
        """
        conn = self.connect
        doms = conn.listAllDomains
        our_domains = [self._libvirt_domain_name(self._node_name(_))
                                            for _ in range(self._meta.num_nodes)]
        for domain_name in our_domains:
            try:
                domain = conn.lookupByName(domain_name)
                if domain.isActive():
                    raise DeploymentRunningError()
                domain.create()
                if domain.isActive():
                    vnc_port = self._domain_graphics_vnc_port_from_xml(domain.XMLDesc(0))
                    logger.info(f'Reach domain {domain_name} at vnc port {vnc_port}')

            except Exception as e:
                logger.error(f'Failed to create domain {domain_name}')
                raise(e)

    def stop(self, force: bool = False) -> None:
        """ Stop Libvirt deployment """
        conn = self.connect
        our_domains = [self._libvirt_domain_name(self._node_name(_))
                                            for _ in range(self._meta.num_nodes)]
        for domain_name in our_domains:
            try:
                logger.debug(f'Looking for {domain_name}')
                domain = conn.lookupByName(domain_name)
                if domain.isActive():
                    logger.info(f'Destroying domain {domain_name}')
                    domain.destroy()
                else:
                    logger.info(f'Domain {domain_name} is not running')
            except Exception as e:
                logger.error(f'{e}')
    @property
    def templates_path(self) -> Path:
        return Path(os.path.dirname(os.path.abspath(__file__)))

    @property
    def domain_template_path(self) -> Path:
        return self.templates_path.joinpath('template_domain.xml.jinja2')

    def get_domain_xml(self, domain_name) -> str:
        template_path = self.domain_template_path
        loader = jinja2.FileSystemLoader(template_path.parent)
        envmnt = jinja2.Environment(loader=loader,
                                    autoescape=jinja2.select_autoescape(['xml']))
        templt = envmnt.get_template(template_path.name)
        disks  = self.get_disks(domain_name, 'default')
        gen = templt.generate(
            domain_name = domain_name,
            disks = disks,
            vnc = self.node_vnc_port(domain_name),
            cdrom = self._meta.cdrom,
        )
        return "".join(gen)

    def remove(self) -> None:
        """ Remove libvirt deployment """
        self._remove_libvirt_domains()
        self._remove()
