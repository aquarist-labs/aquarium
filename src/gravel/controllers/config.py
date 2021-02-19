import os
from enum import Enum
from logging import Logger
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi.logger import logger as fastapi_logger


logger: Logger = fastapi_logger


_env_prefix = "AQUARIUM_"
_env_config_dir = "CONFIG_DIR"
_config_dir_env = os.getenv(f"{_env_prefix}{_env_config_dir}")

config_dir: str = _config_dir_env if _config_dir_env else '/etc/aquarium'


class DeploymentStage(str, Enum):
    none = "none"
    bootstrapping = "bootstrapping"
    bootstrapped = "bootstrapped"
    ready = "ready"


class DeploymentStateModel(BaseModel):
    last_modified: datetime = Field(title="Last Modified")
    stage: DeploymentStage = Field(title="Current Deployment Stage")


class InventoryOptionsModel(BaseModel):
    probe_interval: int = Field(60, title="Inventory Probe Interval")


class StorageOptionsModel(BaseModel):
    probe_interval: float = Field(30.0, title="Storage Probe Interval")


class OptionsModel(BaseModel):
    service_state_path: Path = Field(Path(config_dir).joinpath("storage.json"),
                                     title="Path to Service State file")
    inventory: InventoryOptionsModel = Field(InventoryOptionsModel())
    storage: StorageOptionsModel = Field(StorageOptionsModel())


class ConfigModel(BaseModel):
    version: int = Field(title="Configuration Version")
    name: str = Field(title="Deployment Name")
    deployment_state: DeploymentStateModel = Field(title="Deployment State")
    options: OptionsModel = Field(OptionsModel(), title="Options")


class Config:

    def __init__(self, path: str = config_dir):
        confdir = Path(path)
        self.confpath = confdir.joinpath(Path("config.json"))
        logger.debug(f'Aquarium config dir: {confdir}')

        confdir.mkdir(0o700, parents=True, exist_ok=True)

        if not self.confpath.exists():
            initconf: ConfigModel = ConfigModel(
                version=3,
                name="",
                deployment_state=DeploymentStateModel(
                    last_modified=datetime.now(),
                    stage=DeploymentStage.none
                )
            )
            initconf.options.service_state_path = Path(path).joinpath("storage.json")
            self._saveConfig(initconf)

        self.config: ConfigModel = ConfigModel.parse_file(self.confpath)

    def _saveConfig(self, conf: ConfigModel) -> None:
        logger.debug(f'Writing Aquarium config: {self.confpath}')
        self.confpath.write_text(conf.json(indent=2))

    @property
    def deployment_state(self) -> DeploymentStateModel:
        return self.config.deployment_state

    def set_deployment_stage(self, stage: DeploymentStage) -> None:
        self.config.deployment_state.last_modified = datetime.now()
        self.config.deployment_state.stage = stage
        self._saveConfig(self.config)

    @property
    def options(self) -> OptionsModel:
        return self.config.options
