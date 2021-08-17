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


from typing import Optional


class AqrError(Exception):
    _msg: str
    _errno: Optional[int]

    def __init__(self, msg: str = "", errno: Optional[int] = None):
        self._msg = msg
        self._errno = errno

    @property
    def message(self) -> str:
        return self._msg

    @property
    def errno(self) -> int:
        return self._errno if self._errno else 1


#
# Deployment Errors
#
class DeploymentPathNotFoundError(AqrError):
    pass


class DeploymentExistsError(AqrError):
    pass


class DeploymentNotFoundError(AqrError):
    pass


class DeploymentNotFinishedError(AqrError):
    pass


class DeploymentStatusError(AqrError):
    pass


class EnterDeploymentError(AqrError):
    pass


class DeploymentRunningError(AqrError):
    pass


class DeploymentNotRunningError(AqrError):
    pass


class DeploymentNodeNotRunningError(AqrError):
    pass


class DeploymentNodeDoesNotExistError(AqrError):
    pass


#
# Box Errors
#
class BoxDoesNotExistError(AqrError):
    pass


class BoxAlreadyExistsError(AqrError):
    pass


#
# Misc Errors
#
class BuildsPathNotFoundError(AqrError):
    pass


class RootNotFoundError(AqrError):
    pass


class ImageNotFoundError(AqrError):
    pass


#
# Vagrant Errors
#
class VagrantError(AqrError):
    pass


class VagrantStatusError(VagrantError):
    pass
