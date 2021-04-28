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


from enum import Enum
from pydantic import BaseModel, Field

from gravel.controllers.errors import GravelError
from gravel.controllers.gstate import GlobalState


class NodeStageEnum(int, Enum):
    NONE = 0
    BOOTSTRAPPING = 1
    DEPLOYED = 2
    JOINING = 3
    READY = 4
    ERROR = 5


class DeploymentModel(BaseModel):
    stage: NodeStageEnum = Field(NodeStageEnum.NONE)


class DeploymentError(GravelError):
    pass


class DeploymentState:

    _stage: NodeStageEnum
    _gstate: GlobalState

    def __init__(self, gstate: GlobalState):
        self._gstate = gstate
        self._stage = NodeStageEnum.NONE

        self._load_stage()

        pass

    def _load_stage(self) -> None:
        try:
            dep = self._gstate.config.read_model("deployment", DeploymentModel)
            self._stage = dep.stage
        except FileNotFoundError:
            self._gstate.config.write_model("deployment", DeploymentModel())

    def _save_stage(self) -> None:
        try:
            self._gstate.config.write_model(
                "deployment",
                DeploymentModel(stage=self._stage)
            )
        except Exception as e:
            raise DeploymentError(str(e))

    @property
    def stage(self) -> NodeStageEnum:
        return self._stage

    @property
    def nostage(self) -> bool:
        return self._stage == NodeStageEnum.NONE

    @property
    def bootstrapping(self) -> bool:
        return self._stage == NodeStageEnum.BOOTSTRAPPING

    @property
    def joining(self) -> bool:
        return self._stage == NodeStageEnum.JOINING

    @property
    def deployed(self) -> bool:
        return self._stage == NodeStageEnum.DEPLOYED

    @property
    def ready(self) -> bool:
        return self._stage == NodeStageEnum.READY

    @property
    def error(self) -> bool:
        return self._stage == NodeStageEnum.ERROR

    def can_start(self) -> bool:
        return (
            self._stage == NodeStageEnum.NONE or
            self._stage == NodeStageEnum.DEPLOYED or
            self._stage == NodeStageEnum.READY
        )

    def mark_bootstrap(self) -> None:
        assert self.nostage
        self._stage = NodeStageEnum.BOOTSTRAPPING
        self._save_stage()

    def mark_join(self) -> None:
        assert not self.joining
        assert not self.error
        self._stage = NodeStageEnum.JOINING
        self._save_stage()

    def mark_deployed(self) -> None:
        assert not self.error
        self._stage = NodeStageEnum.DEPLOYED
        self._save_stage()

    def mark_error(self) -> None:
        self._stage = NodeStageEnum.ERROR
        self._save_stage()

    def mark_ready(self) -> None:
        assert not self.error
        self._stage = NodeStageEnum.READY
        self._save_stage()
