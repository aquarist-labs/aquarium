from enum import Enum
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field


class DeploymentStage(str, Enum):
    none = "none"
    bootstrapping = "bootstrapping"
    bootstrapped = "bootstrapped"
    ready = "ready"


class DeploymentStateModel(BaseModel):
    last_modified: datetime = Field(title="Last Modified")
    stage: DeploymentStage = Field(title="Current Deployment Stage")


class ConfigModel(BaseModel):
    version: int = Field(title="Configuration Version")
    name: str = Field(title="Deployment Name")
    deployment_state: DeploymentStateModel = Field(title="Deployment State")


class Config:

    def __init__(self, path: str = "/etc/aquarium"):
        confdir = Path(path)
        self.confpath = confdir.joinpath(Path("config.json"))

        confdir.mkdir(0o700, parents=True, exist_ok=True)

        if not self.confpath.exists():
            initconf: ConfigModel = ConfigModel(
                version=1,
                name="",
                deployment_state=DeploymentStateModel(
                    last_modified=datetime.now(),
                    stage=DeploymentStage.none
                )
            )
            self._saveConfig(initconf)

        self.config: ConfigModel = ConfigModel.parse_file(self.confpath)

    def _saveConfig(self, conf: ConfigModel) -> None:
        self.confpath.write_text(conf.json(indent=2))

    @property
    def deployment_state(self) -> DeploymentStateModel:
        return self.config.deployment_state

    def set_deployment_stage(self, stage: DeploymentStage) -> None:
        self.config.deployment_state.last_modified = datetime.now()
        self.config.deployment_state.stage = stage
        self._saveConfig(self.config)
