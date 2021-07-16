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
from typing import Type, TypeVar
from pydantic import BaseModel, Field
from typing import Optional

from fastapi.logger import logger as fastapi_logger

from . import utils

logger: Logger = fastapi_logger


def _get_default_confdir() -> str:
    _env_prefix = "AQUARIUM_"
    _env_config_dir = "CONFIG_DIR"
    _config_dir_env = os.getenv(f"{_env_prefix}{_env_config_dir}")

    config_dir: str = _config_dir_env if _config_dir_env else "/etc/aquarium"
    return config_dir


class InventoryOptionsModel(BaseModel):
    probe_interval: int = Field(60, title="Inventory Probe Interval")


class StorageOptionsModel(BaseModel):
    probe_interval: float = Field(30.0, title="Storage Probe Interval")


class DevicesOptionsModel(BaseModel):
    probe_interval: float = Field(5.0, title="Devices Probe Interval")


class StatusOptionsModel(BaseModel):
    probe_interval: float = Field(1.0, title="Status Probe Interval")


class ServicesOptionsModel(BaseModel):
    probe_interval: float = Field(1.0, title="Services Probe Interval")


class EtcdOptionsModel(BaseModel):
    registry: str = Field(
        "quay.io/coreos/etcd", title="Container Image Registry"
    )
    version: str = Field("latest", title="Container Version Label")
    data_dir: str = Field("/var/lib/etcd", title="Etcd Data Dir")


class AuthOptionsModel(BaseModel):
    jwt_secret: str = Field(
        title="The access token secret",
        default_factory=lambda: utils.random_string(24),
    )
    jwt_ttl: int = Field(
        36000, title="How long an access token should live before it expires"
    )


class OptionsModel(BaseModel):
    service_state_path: Path = Field(
        Path(_get_default_confdir()).joinpath("storage.json"),
        title="Path to Service State file",
    )
    inventory: InventoryOptionsModel = Field(InventoryOptionsModel())
    storage: StorageOptionsModel = Field(StorageOptionsModel())
    devices: DevicesOptionsModel = Field(DevicesOptionsModel())
    status: StatusOptionsModel = Field(StatusOptionsModel())
    services: ServicesOptionsModel = Field(ServicesOptionsModel())
    etcd: EtcdOptionsModel = Field(EtcdOptionsModel())
    auth: AuthOptionsModel = Field(AuthOptionsModel())


class ConfigModel(BaseModel):
    version: int = Field(title="Configuration Version")
    name: str = Field(title="Deployment Name")
    options: OptionsModel = Field(OptionsModel(), title="Options")


class Config:
    def __init__(self, path: Optional[str] = None):
        if not path:
            path = _get_default_confdir()
        self._confdir = Path(path)
        self.confpath = self._confdir.joinpath(Path("config.json"))
        logger.debug(f"Aquarium config dir: {self._confdir}")

        self._confdir.mkdir(0o700, parents=True, exist_ok=True)

        if not self.confpath.exists():
            initconf: ConfigModel = ConfigModel(version=1, name="")
            initconf.options.service_state_path = Path(path).joinpath(
                "storage.json"
            )
            self._saveConfig(initconf)

        self.config: ConfigModel = ConfigModel.parse_file(self.confpath)

    def _saveConfig(self, conf: ConfigModel) -> None:
        logger.debug(f"Writing Aquarium config: {self.confpath}")
        self.confpath.write_text(conf.json(indent=2))

    @property
    def options(self) -> OptionsModel:
        return self.config.options

    @property
    def confdir(self) -> Path:
        return self._confdir

    T = TypeVar("T")

    def read_model(self, name: str, model: Type[T]) -> T:
        return utils.read_model(self.confdir, name, model)

    def write_model(self, name: str, value: BaseModel) -> None:
        utils.write_model(self.confdir, name, value)
