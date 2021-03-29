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
from logging import Logger
from pathlib import Path
from pydantic import BaseModel, Field
from fastapi.logger import logger as fastapi_logger


logger: Logger = fastapi_logger


_env_prefix = "AQUARIUM_"
_env_config_dir = "CONFIG_DIR"
_config_dir_env = os.getenv(f"{_env_prefix}{_env_config_dir}")

config_dir: str = _config_dir_env if _config_dir_env else '/etc/aquarium'


class InventoryOptionsModel(BaseModel):
    probe_interval: int = Field(60, title="Inventory Probe Interval")


class StorageOptionsModel(BaseModel):
    probe_interval: float = Field(30.0, title="Storage Probe Interval")


class DevicesOptionsModel(BaseModel):
    probe_interval: float = Field(30.0, title="Devices Probe Interval")


class StatusOptionsModel(BaseModel):
    probe_interval: float = Field(1.0, title="Status Probe Interval")


class EventsOptionsModel(BaseModel):
    tick_interval: float = Field(30.0, title="Events Probe Interval")
    ttl: int = Field(3600, title="Number of seconds an event is valid for")
    queue_max: int = Field(100, title="Maximum number of events to keep")


class OptionsModel(BaseModel):
    service_state_path: Path = Field(Path(config_dir).joinpath("storage.json"),
                                     title="Path to Service State file")
    inventory: InventoryOptionsModel = Field(InventoryOptionsModel())
    storage: StorageOptionsModel = Field(StorageOptionsModel())
    devices: DevicesOptionsModel = Field(DevicesOptionsModel())
    status: StatusOptionsModel = Field(StatusOptionsModel())
    events: EventsOptionsModel = Field(EventsOptionsModel())


class ConfigModel(BaseModel):
    version: int = Field(title="Configuration Version")
    name: str = Field(title="Deployment Name")
    options: OptionsModel = Field(OptionsModel(), title="Options")


class Config:

    def __init__(self, path: str = config_dir):
        self._confdir = Path(path)
        self.confpath = self._confdir.joinpath(Path("config.json"))
        logger.debug(f'Aquarium config dir: {self._confdir}')

        self._confdir.mkdir(0o700, parents=True, exist_ok=True)

        if not self.confpath.exists():
            initconf: ConfigModel = ConfigModel(
                version=1,
                name=""
            )
            initconf.options.service_state_path = Path(path).joinpath("storage.json")
            self._saveConfig(initconf)

        self.config: ConfigModel = ConfigModel.parse_file(self.confpath)

    def _saveConfig(self, conf: ConfigModel) -> None:
        logger.debug(f'Writing Aquarium config: {self.confpath}')
        self.confpath.write_text(conf.json(indent=2))

    @property
    def options(self) -> OptionsModel:
        return self.config.options

    @property
    def confdir(self) -> Path:
        return self._confdir
