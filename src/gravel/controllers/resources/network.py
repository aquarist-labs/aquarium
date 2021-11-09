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

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from atomicwrites import atomic_write
from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field

from gravel.controllers.gstate import Ticker
from gravel.controllers.utils import aqr_run_cmd

logger: logging.Logger = fastapi_logger


class InterfaceConfigModel(BaseModel):
    # Simplified "UI friendly" version of the actual config, i.e. we're not
    # exposing everything in /etc/sysconfig/network/ifcfg-*, only the bits that
    # we want the user to be able to change.
    # TODO: bootproto would be better as a StrEnum (so we could force "dhcp" or "static")
    bootproto: str = Field("dhcp", title="Boot Protocol")
    ipaddr: Optional[str] = Field("", title="IP Address")
    # If bonding_slaves is _not_ empty, this interface is a bonding master.
    bonding_slaves: Optional[List] = Field(
        [], title="Bonding slave network interfaces"
    )
    # TODO: Expose bonding module options


# This is actually useful to have, because the interface might not *have* any config yet,
# and in future we might want to see statistics, state (up/down, etc.) which would all
# belong in this model.  OTOH, if we can get stats from cephadm, maybe this should be
# dropped and we just do a dict of InterfaceConfigModels instead, and drop this extra
# layer.
class InterfaceModel(BaseModel):
    name: str = Field(title="Logical Name")
    config: Optional[InterfaceConfigModel] = Field(
        None, title="Interface config"
    )
    # TODO: could add stats, current state etc. here but note that this would
    # duplicate information available via /api/local/nodeinfo (which comes from cephadm)


class RouteModel(BaseModel):
    destination: str = Field("default", title="Destination")
    gateway: str = Field("-", title="Gateway")
    interface: str = Field("-", title="Interface")


class Network(Ticker):

    _interfaces: Dict[str, InterfaceModel] = {}
    _nameservers: List[str] = []
    _routes: List[RouteModel] = []
    _is_busy: bool = False

    def __init__(self, interval: float) -> None:
        super().__init__(interval)

    @property
    def interfaces(self) -> Dict[str, InterfaceModel]:
        return self._interfaces

    @property
    def nameservers(self) -> List[str]:
        return self._nameservers

    @property
    def routes(self) -> List[RouteModel]:
        return self._routes

    async def _do_tick(self) -> None:
        self._refresh_interfaces()
        self._refresh_nameservers()
        self._refresh_routes()
        logger.debug(self._interfaces)
        logger.debug(self._nameservers)
        logger.debug(self._routes)

    async def _should_tick(self) -> bool:
        return not self._is_busy

    def _refresh_interfaces(self) -> None:
        # interfaces is the union of the physical interfaces (/sys/class/net/...) and
        # any interfaces for which we have config files (/etc/sysconfig/network/ifcfg-*)
        interfaces: Dict[str, InterfaceModel] = {}

        # This gets the physical interfaces
        sys_class_net = Path("/sys/class/net")
        assert sys_class_net.exists() and sys_class_net.is_dir()
        for dev in sys_class_net.glob("*"):
            device = dev.joinpath("device")
            if device.exists():
                # /sys/class/net/$dev/device exist, so it's a physical interface
                interfaces[dev.stem] = InterfaceModel(name=dev.stem)

        # ...and this gets any configured interfaces
        sysconfig = Path("/etc/sysconfig/network")
        assert sysconfig.exists() and sysconfig.is_dir()
        for conf in sysconfig.glob("ifcfg-*"):
            # Blacklist here is lifted from wicked source
            if conf.name.endswith("~") or conf.suffix in [
                ".old",
                ".bak",
                ".orig",
                ".scpmbackup",
                ".rpmnew",
                ".rpmsave",
                ".rpmorig",
            ]:
                logger.debug(f"Skipping blacklisted suffix on {conf}")
                continue
            iface = conf.stem[6:]
            if iface == "lo":
                # We don't care about the loopback interface
                continue
            logger.debug(f"Reading {iface} config from {conf}")

            rawconf = self._parse_config(conf)

            config = InterfaceConfigModel()
            if "IPADDR" in rawconf:
                rawaddr = rawconf["IPADDR"]
                if rawaddr:
                    config.ipaddr = rawaddr
                    # TODO: do we want to separate netmask etc. out?
                    # (it can currently only be specified as "/" suffix
                    # on ipaddr)
            if "BOOTPROTO" in rawconf and rawconf["BOOTPROTO"] is not None:
                config.bootproto = rawconf["BOOTPROTO"]

            if iface not in interfaces:
                interfaces[iface] = InterfaceModel(name=iface)
            interfaces[iface].config = config

        self._interfaces = interfaces

    def _refresh_nameservers(self) -> None:
        config = Path("/etc/sysconfig/network/config")
        assert config.exists() and config.is_file()
        rawconf = self._parse_config(config)
        if (
            "NETCONFIG_DNS_STATIC_SERVERS" in rawconf
            and rawconf["NETCONFIG_DNS_STATIC_SERVERS"] is not None
        ):
            self._nameservers = rawconf["NETCONFIG_DNS_STATIC_SERVERS"].split()
        else:
            self._nameservers = []

    def _refresh_routes(self) -> None:
        routes: List[RouteModel] = []
        route_paths = [Path("/etc/sysconfig/network/routes")]
        for iface in self._interfaces:
            route_paths.append(Path(f"/etc/sysconfig/network/ifroute-{iface}"))
        for path in route_paths:
            if not path.exists():
                continue
            with path.open("r") as f:
                for line in f.readlines():
                    stripped = line.strip()
                    if len(stripped) == 0 or stripped.startswith("#"):
                        continue
                    fields = stripped.split()
                    routes.append(
                        RouteModel(
                            destination=fields[0],
                            gateway=fields[1],
                            interface=fields[3],
                        )
                    )
        self._routes = routes

    def _parse_config(self, path: Path) -> Dict[str, Optional[str]]:
        with path.open("r") as f:
            contents = f.readlines()
        rawconf: Dict[str, Optional[str]] = {}
        for line in contents:
            stripped = line.strip()
            if len(stripped) == 0 or stripped.startswith("#"):
                continue
            first, second = stripped.split("=", maxsplit=1)
            field = first.strip()
            value = second.strip().strip("'\"")
            assert len(field) > 0
            rawconf[field] = value if len(value) > 0 else None
        return rawconf

    def _update_config(self, path: Path, new_config: Dict[str, str]):
        with path.open("r") as fin, atomic_write(path, overwrite=True) as fout:
            for line in fin:
                stripped = line.strip()
                if len(stripped) > 0 and not stripped.startswith("#"):
                    first, second = stripped.split("=", maxsplit=1)
                    field = first.strip()
                    if field in new_config:
                        # TODO: doesn't handle embedded quotes (but we're unlikely to care right now)
                        line = f'{field}="{new_config[field]}"\n'
                fout.write(line)

    def _update_route_file(
        self, path: Path, interface: str, routes: List[RouteModel]
    ):
        if routes:
            with atomic_write(path, overwrite=True) as f:
                for route in routes:
                    f.write(
                        f"{route.destination} {route.gateway} - {route.interface}\n"
                    )
        else:
            # No routes for this interface, delete config file if present
            path.unlink(missing_ok=True)

    async def apply_config(
        self,
        interfaces: Dict[str, InterfaceModel],
        nameservers: List[str],
        routes: List[RouteModel],
    ) -> None:
        logger.debug("In Network.apply_config()")
        self._is_busy = True
        sysconfig = Path("/etc/sysconfig/network")

        bonding_slave_interfaces: List[str] = []
        for iface in interfaces:
            conf = sysconfig.joinpath(f"ifcfg-{iface}")
            new_config = interfaces[iface].config
            if new_config is None:
                # interface with no config, so get rid of it
                conf.unlink(missing_ok=True)
                continue
            # This is destructive of any existing config
            # (i.e. we're not mergeing here, we're clobbering)
            logger.info(f"Writing {conf}")
            with atomic_write(conf, overwrite=True) as f:
                f.write(
                    f"STARTMODE='auto'\n"
                    f"BOOTPROTO='{new_config.bootproto}'\n"
                    f"IPADDR='{new_config.ipaddr}'\n"
                )
                if new_config.bonding_slaves:
                    f.write("BONDING_MASTER='yes'\n")
                    for i, s in enumerate(new_config.bonding_slaves):
                        f.write(f"BONDING_SLAVE{i}='{s}'\n")
                        bonding_slave_interfaces.append(s)
                    f.write(
                        "BONDING_MODULE_OPTS='mode=active-backup miimon=100'\n"
                    )
        # special case for bonding slave interfaces, if any, which need to be
        # overwritten with STARTMODE=hotplug, BOOTPROTO=none
        for iface in bonding_slave_interfaces:
            conf = sysconfig.joinpath(f"ifcfg-{iface}")
            logger.info(f"Writing {conf}")
            with atomic_write(conf, overwrite=True) as f:
                f.write("STARTMODE='hotplug'\nBOOTPROTO='none'\n")
        self._refresh_interfaces()

        # Write nameserver config
        self._update_config(
            Path("/etc/sysconfig/network/config"),
            {"NETCONFIG_DNS_STATIC_SERVERS": " ".join(nameservers)},
        )
        self._refresh_nameservers()

        # Write route config
        for iface in self._interfaces:
            self._update_route_file(
                Path(f"/etc/sysconfig/network/ifroute-{iface}"),
                iface,
                [route for route in routes if route.interface == iface],
            )
        self._update_route_file(
            Path("/etc/sysconfig/network/routes"),
            "-",
            [route for route in routes if route.interface == "-"],
        )
        self._refresh_routes()

        logger.info("Restarting network services...")
        ret, _, err = await aqr_run_cmd(
            ["systemctl", "restart", "network.service"]
        )
        # TODO: can this fail?
        logger.info("Restarted network services")
        self._is_busy = False
