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
import shlex
import psutil
from datetime import datetime as dt
from typing import Any, Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field, parse_raw_as
from fastapi.logger import logger as fastapi_logger

from gravel.controllers.errors import GravelError
from gravel.controllers.gstate import Ticker
from gravel.controllers.utils import aqr_run_cmd


logger: logging.Logger = fastapi_logger


class InterfacesError(GravelError):
    pass


class HardwareListError(InterfacesError):
    pass


class UnknownInterfaceError(InterfacesError):
    pass


class RawIFaceConfigModel(BaseModel):
    autonegotiation: str
    broadcast: str
    driver: str
    driverversion: str
    firmware: str
    latency: int
    link: str
    multicast: str
    port: str
    ip: Optional[str]
    speed: Optional[str]


class RawIFaceModel(BaseModel):
    id: str
    claimed: bool
    handle: str
    description: str
    product: str
    vendor: str
    businfo: str
    logicalname: str
    version: int
    serial: str
    units: str
    capacity: int
    configuration: RawIFaceConfigModel


class InterfaceDeviceDriverModel(BaseModel):
    driver: str = Field("", title="driver used by device")
    version: str = Field("", title="driver version")


class InterfaceDeviceModel(BaseModel):
    description: str = Field(title="Interface description")
    product: str = Field(title="Interface Product Name")
    vendor: str = Field(title="Interface Vendor")
    driver: InterfaceDeviceDriverModel = Field(InterfaceDeviceDriverModel())
    firmware: str = Field(title="Device's firmware")
    address: str = Field(title="Physical Address")
    capacity: int = Field(title="Capacity in bits per second")


class InterfaceCapsModel(BaseModel):
    autonegotiation: bool = Field(False, title="Auto negotiation")
    broadcast: bool = Field(False, title="Broadcast")
    multicast: bool = Field(False, title="Multicast")


class InterfaceConfigModel(BaseModel):
    address: Optional[str] = Field(None, title="IP address")
    prefixlen: Optional[int] = Field(None, title="IP address prefix length")
    bootproto: Optional[str] = Field(
        None, title="Mode the interface will be set up"
    )
    startmode: Optional[str] = Field(
        None, title="When the interface should be set up"
    )


class PCIBusInfoModel(BaseModel):
    raw: str = Field("", title="Device's raw PCI BDF")
    domain: int = Field(0, title="PCI Domain")
    bus: int = Field(0, title="Device's PCI bus")
    device: int = Field(0, title="Device's PCI bus' device")
    function: int = Field(0, title="Device's PCI bus' function")

    def get_bus_id(self) -> str:
        return f"{self.domain}:{self.bus}"


class InterfaceModel(BaseModel):
    pci: PCIBusInfoModel = Field(PCIBusInfoModel(), title="PCI bus info")
    device: InterfaceDeviceModel = Field(title="details about physical device")
    name: str = Field(title="Logical Name")
    address: Optional[str] = Field(None, title="IP Address")
    speed: int = Field(0, title="Current speed in bits per second")
    link: bool = Field(False, title="Interface has a link")
    caps: InterfaceCapsModel = Field(title="Configuration details")
    config: InterfaceConfigModel = Field(
        InterfaceConfigModel(), title="Interface config"
    )


class NetworkCardModel(BaseModel):
    domain: int = Field(0, title="PCI domain")
    bus: int = Field(0, title="Device's PCI bus")
    ports: List[InterfaceModel] = Field([], title="Ports per network card")


class InterfaceStatsModel(BaseModel):
    tx: int = Field(0, title="Sent bytes")
    rx: int = Field(0, title="Received bytes")
    ts: int = Field(0, title="Reading timestamp")


def _get_speed(v: Optional[str]) -> int:
    """Obtain speed in bytes from string"""
    if not v:
        return 0
    power = 0
    if v.lower().endswith("gbit/s"):
        power = 3
    elif v.lower().endswith("mbit/s"):
        power = 2
    elif v.lower().endswith("kbit/s"):
        power = 1
    vstr = ""
    for c in v:
        if c.isdigit():
            vstr += c
    if len(vstr) == 0:
        raise ValueError()
    return int(vstr) * pow(1000, power)


class Interfaces(Ticker):

    sysconf = "/etc/sysconfig/network"

    """ Network Interface mapping, by interface name """
    _interface_by_name: Dict[str, InterfaceModel] = {}
    """ Network Cards, indexed by pci bus """
    _network_cards: Dict[str, NetworkCardModel] = {}
    """ Statistics by network interface, in bytes/second """
    _statistics_by_name: Dict[str, List[InterfaceStatsModel]] = {}
    """ Last obtained statistics, per interface, in bytes """
    _last_statistics: Dict[str, InterfaceStatsModel] = {}

    def __init__(self, interval: float) -> None:
        super().__init__(interval)

    async def _do_tick(self) -> None:
        await self._update_network_cards()
        self._cleanup_statistics()
        self._update_statistics()

    async def _should_tick(self) -> bool:
        return True

    async def _get_raw_devices(self) -> List[RawIFaceModel]:
        """Obtain raw interfaces, as provided by lshw"""
        cmd = "lshw -class network -json"
        ret, stdout, stderr = await aqr_run_cmd(shlex.split(cmd))
        if ret != 0:
            raise HardwareListError(stderr)
        if not stdout:
            raise HardwareListError("no return")
        return parse_raw_as(List[RawIFaceModel], stdout)

    def _raw_to_iface(self, raw: RawIFaceModel) -> InterfaceModel:
        """Transform a raw interface, as provided by lshw, to our model"""

        def _get_bool(v: str) -> bool:
            if v == "on" or v == "true" or v == "yes":
                return True
            return False

        def _get_pci() -> PCIBusInfoModel:
            rawpci = raw.handle
            fields = rawpci.split(":")
            assert len(fields) == 4
            domain = fields[1]
            bus = fields[2]
            device, function = fields[3].split(".")
            return PCIBusInfoModel(
                raw=rawpci,
                domain=int(domain),
                bus=int(bus),
                device=int(device),
                function=int(function),
            )

        return InterfaceModel(
            pci=_get_pci(),
            device=InterfaceDeviceModel(
                description=raw.description,
                product=raw.product,
                vendor=raw.vendor,
                driver=InterfaceDeviceDriverModel(
                    driver=raw.configuration.driver,
                    version=raw.configuration.driverversion,
                ),
                firmware=raw.configuration.firmware,
                address=raw.serial,
                capacity=raw.capacity,
            ),
            name=raw.logicalname,
            address=raw.configuration.ip,
            speed=_get_speed(raw.configuration.speed),
            link=_get_bool(raw.configuration.link),
            caps=InterfaceCapsModel(
                autonegotiation=_get_bool(raw.configuration.autonegotiation),
                broadcast=_get_bool(raw.configuration.broadcast),
                multicast=_get_bool(raw.configuration.multicast),
            ),
        )

    def _get_network_config(self, iface: str) -> InterfaceConfigModel:
        """Obtain a specific interface's configuration from /etc/sysconfig"""
        sysconf = Path(self.sysconf)
        assert sysconf.exists() and sysconf.is_dir()

        netconf = Path(f"{sysconf}/ifcfg-{iface}")
        if not netconf.exists():
            raise UnknownInterfaceError(iface)

        with netconf.open(mode="r") as f:
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
            rawconf[field.lower()] = value if len(value) > 0 else None

        conf = InterfaceConfigModel()
        if "ipaddr" in rawconf:
            rawaddr = rawconf["ipaddr"]
            if rawaddr:
                conf.address = rawaddr
                if "/" in rawaddr:
                    addr, prefix = rawaddr.split("/", maxsplit=1)
                    conf.address = addr
                    conf.prefixlen = int(prefix)
        if "bootproto" in rawconf:
            conf.bootproto = rawconf["bootproto"]
        if "startmode" in rawconf:
            conf.startmode = rawconf["startmode"]

        return conf

    async def _update_network_cards(self) -> None:
        """Update known network cards and their interfaces"""
        raw_ifaces: List[RawIFaceModel] = await self._get_raw_devices()
        ifaces: Dict[str, InterfaceModel] = {}
        cards: Dict[str, NetworkCardModel] = {}

        for raw in raw_ifaces:
            iface: InterfaceModel = self._raw_to_iface(raw)
            ifaces[iface.name] = iface
            iface.config = self._get_network_config(iface.name)

            busid = iface.pci.get_bus_id()
            if busid not in cards:
                cards[busid] = NetworkCardModel(
                    domain=iface.pci.domain, bus=iface.pci.bus, ports=[]
                )
            cards[busid].ports.append(iface)

        self._network_cards = cards
        self._interface_by_name = ifaces

    def _get_timestamp(self) -> int:
        """Obtain current timestamp. Standalone function, meant to mock."""
        return int(dt.timestamp(dt.utcnow()))

    def _update_statistics(self) -> None:
        """Update known interfaces' statistics"""
        counters: Dict[str, Any] = psutil.net_io_counters(  # type: ignore
            pernic=True, nowrap=True
        )
        for name, cnt in counters.items():
            if name not in self._interface_by_name:
                continue
            recv: int = cnt.bytes_recv
            sent: int = cnt.bytes_sent
            ts: int = self._get_timestamp()
            last = self._last_statistics.get(name)
            self._last_statistics[name] = InterfaceStatsModel(
                tx=sent, rx=recv, ts=ts
            )
            if not last:
                continue

            dts = ts - last.ts
            tx = round(float((sent - last.tx) / dts), 2)
            rx = round(float((recv - last.rx) / dts), 2)
            if name not in self._statistics_by_name:
                self._statistics_by_name[name] = []
            self._statistics_by_name[name].append(
                InterfaceStatsModel(tx=tx, rx=rx, ts=ts)
            )

    def _cleanup_statistics(self) -> None:
        """Remove unknown interfaces from statistics"""
        to_remove: List[str] = [
            iface
            for iface in self._statistics_by_name.keys()
            if iface not in self._interface_by_name
        ]
        for iface in to_remove:
            del self._statistics_by_name[iface]

    @property
    def stats(self) -> Dict[str, List[InterfaceStatsModel]]:
        """Obtain all statistics, by interface, in bytes per second"""
        return self._statistics_by_name

    @property
    def interfaces(self) -> Dict[str, InterfaceModel]:
        """Obtain all interfaces, by name"""
        return self._interface_by_name

    @property
    def cards(self) -> Dict[str, NetworkCardModel]:
        """Obtain all network cards, by bus id"""
        return self._network_cards

    def get_interface(self, name: str) -> InterfaceModel:
        """Obtain a single interface, by name"""
        iface = self._interface_by_name.get(name)
        if not iface:
            raise UnknownInterfaceError(name)
        return iface

    def get_statistics(self, name: str) -> List[InterfaceStatsModel]:
        """Obtain statistics for a single interface, in bytes per second"""
        stats = self._statistics_by_name.get(name)
        if not stats:
            raise UnknownInterfaceError(name)
        return stats
