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
from typing import Dict, Optional, Type, TypeVar

from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, Field

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


class NetworkOptionsModel(BaseModel):
    probe_interval: float = Field(5.0, title="Network Probe Interval")


class AuthOptionsModel(BaseModel):
    jwt_secret: str = Field(
        title="The access token secret",
        default_factory=lambda: utils.random_string(24),
    )
    jwt_ttl: int = Field(
        36000, title="How long an access token should live before it expires"
    )


class ContainersOptionsModel(BaseModel):
    registry: str = Field("registry.opensuse.org", title="Registry to use")
    image: str = Field(
        "filesystems/ceph/master/upstream/images/opensuse/ceph/ceph:latest",
        title="Container image",
    )
    secure: bool = Field(True, title="Whether the registry is secure")

    def get_image(self) -> str:
        assert self.registry is not None and len(self.registry) > 0
        assert self.image is not None and len(self.image) > 0
        return f"{self.registry}/{self.image}"


class OptionsModel(BaseModel):
    inventory: InventoryOptionsModel = Field(InventoryOptionsModel())
    storage: StorageOptionsModel = Field(StorageOptionsModel())
    devices: DevicesOptionsModel = Field(DevicesOptionsModel())
    status: StatusOptionsModel = Field(StatusOptionsModel())
    network: NetworkOptionsModel = Field(NetworkOptionsModel())
    auth: AuthOptionsModel = Field(AuthOptionsModel())
    containers: ContainersOptionsModel = Field(ContainersOptionsModel())


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

    def init(self) -> None:
        self._confdir.mkdir(0o700, parents=True, exist_ok=True)

        if not self.confpath.exists():
            initconf: ConfigModel = ConfigModel(version=1, name="")
            self._saveConfig(initconf)

        self.config: ConfigModel = ConfigModel.parse_file(self.confpath)
        self._registry_config_from_env()

    def _registry_config_from_env(self):
        keys: Dict[Optional[str], str] = {}
        for k in ["URL", "IMAGE", "SECURE"]:
            env: str = f"AQUARIUM_REGISTRY_{k}"
            value: Optional[str] = os.getenv(env, None)
            if value is None:
                continue
            if len(value) == 0:
                logger.error(f"value for custom registry conf {env} is empty")
                continue
            keys[k.lower()] = value

        if "url" in keys:
            self.config.options.containers.registry = keys["url"]
        if "image" in keys:
            self.config.options.containers.image = keys["image"]
        if "secure" in keys:
            raw = keys["secure"].lower()
            v: bool = raw == "true" or raw == "1"
            self.config.options.containers.secure = v
        if len(keys) > 0:
            logger.warning("Using custom registry config from environment")

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
