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

from typing import Optional


class NodeError(Exception):
    def __init__(self, msg: Optional[str] = ""):
        super().__init__()
        self._msg = msg


class NodeNotStartedError(NodeError):
    pass


class NodeShuttingDownError(NodeError):
    pass


class NodeBootstrappingError(NodeError):
    pass


class NodeHasBeenDeployedError(NodeError):
    pass


class NodeAlreadyJoiningError(NodeError):
    pass


class NodeHasJoinedError(NodeError):
    pass


class NodeCantBootstrapError(NodeError):
    pass
