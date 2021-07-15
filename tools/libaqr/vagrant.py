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

import os
import subprocess
import shlex
import errno
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger: logging.Logger = logging.getLogger("aquarium")


from libaqr.errors import (
    BoxAlreadyExistsError,
    DeploymentNodeDoesNotExistError,
    DeploymentNodeNotRunningError,
    DeploymentNotFinishedError,
    VagrantError,
    VagrantStatusError
)


class VagrantStateEnum(int, Enum):
    NONE = 0,
    RUNNING = 1,
    PREPARING = 2,
    NOT_CREATED = 3,
    SHUTOFF = 4


class Vagrant:

    _path: Optional[Path]

    def __init__(self, path: Optional[Path] = None):
        self._path = path

    def start(self, conservative: bool) -> Tuple[bool, Optional[str]]:

        cmd = "vagrant up"
        if conservative:
            cmd += " --no-parallel --no-destroy-on-error"

        retcode, _, err = self._run(cmd, interactive=True)
        if retcode != 0:
            return False, err
        return True, None

    def stop(self, interactive: bool = True) -> Tuple[bool, Optional[str]]:
        cmd = "vagrant destroy"
        if not interactive:
            cmd += " --force"
        retcode, _, err = self._run(cmd, interactive=True)
        if retcode != 0:
            return False, err
        return True, None

    def shell(self, node: Optional[str], command: Optional[str]) -> int:
        cmd = "vagrant ssh"
        if node:
            cmd += f" {node}"
        if command:
            cmd += f" -c '{command}'"

        found = False
        for node_name, node_state in self.nodes_status:
            if node == node_name:
                if node_state != VagrantStateEnum.RUNNING:
                    raise DeploymentNodeNotRunningError(node_name)
                found = True
                break
        if node and not found:
            raise DeploymentNodeDoesNotExistError(node)

        retcode, _, _ = self._run(cmd, interactive=True)
        return retcode

    @classmethod
    def box_list(cls) -> List[Tuple[str,str]]:
        """ List all known vagrant boxes with the provider, including unrelated to aquarium. """

        logger.debug(f"boxlist.......")

        cmd = "vagrant box list --machine-readable"
        retcode, out, err = cls.run(None, cmd, interactive=False)
        if retcode != 0:
            raise VagrantError(msg=err, errno=retcode)

        boxes = [name for name in out.splitlines() if name.count("box-name") > 0]
        providers = [provider for provider in out.splitlines() if provider.count("box-provider") > 0]
        boxlist: List[Tuple[str,str]] = []
        for box_entry, provider_entry in zip(boxes, providers):
            boxname = box_entry.split(",")[3]
            provider = provider_entry.split(",")[3]
            logger.debug(f"boxname: {boxname}, provider: {provider}")
            boxlist.append((boxname, provider))
        return boxlist

    @classmethod
    def box_remove(cls, name: str, provider: str='libvirt') -> None:
        """ Remove an existing box """
        if [name, provider] not in cls.box_list():
            return

        cmd = f"vagrant box remove {name} --provider {provider}"
        retcode, _, err = cls.run(None, cmd, interactive=False)
        if retcode != 0:
            raise VagrantError(
                msg=f"failed removing box '{name}' ({provider}): {err}",
                errno=retcode
            )

    @classmethod
    def box_add(cls, name: str, path: Path, provider: str='libvirt') -> None:
        """ Add image from 'path' as box 'name', different 'provider' could have the same 'name' """

        avail_boxes = cls.box_list()
        if [name, provider] in avail_boxes:
            raise BoxAlreadyExistsError()

        cmd = f"vagrant box add {name} {path}"
        retcode, _, err = cls.run(None, cmd, interactive=False)
        if retcode != 0:
            raise VagrantError(
                msg=f"failed adding box '{name}': {err}",
                errno=retcode
            )

    @classmethod
    def run(
        cls,
        env_path: Optional[Path],
        cmd: str,
        interactive: bool
    ) -> Tuple[int, str, str]:
        inst = cls(env_path)
        return inst._run(cmd, interactive)

    @property
    def nodes_status(self) -> List[Tuple[str, VagrantStateEnum]]:
        cmd = "vagrant status --machine-readable"

        retcode, out, err = self._run(cmd)
        if retcode != 0:
            raise VagrantStatusError(err, errno=retcode)

        metadata = self._parse_vagrant(out)
        if "state" not in metadata:
            raise VagrantStatusError("unknown state", errno=errno.EINVAL)

        nodes_state: List[Tuple[str, VagrantStateEnum]] = []
        state_per_node = metadata["state"]

        for node, node_state in state_per_node:
            state = VagrantStateEnum.NONE
            if node_state == "running":
                state = VagrantStateEnum.RUNNING
            elif node_state == "preparing":
                state = VagrantStateEnum.PREPARING
            elif node_state == "shutoff":
                state = VagrantStateEnum.SHUTOFF
            elif node_state == "not_created":
                state = VagrantStateEnum.NOT_CREATED

            nodes_state.append((node, state))

        return nodes_state

    @property
    def running(self) -> bool:
        return VagrantStateEnum.RUNNING in self._status()

    @property
    def preparing(self) -> bool:
        return VagrantStateEnum.PREPARING in self._status()

    @property
    def shutoff(self) -> bool:
        return VagrantStateEnum.SHUTOFF in self._status()

    @property
    def notcreated(self) -> bool:
        return VagrantStateEnum.NOT_CREATED in self._status()

    @contextmanager
    def safeenv(self):
        try:
            env = os.environ.copy()
            if self._path:
                env["VAGRANT_CWD"] = str(self._path)
            yield env
        finally:
            pass

    def _status(self) -> List[VagrantStateEnum]:
        return [status for _, status in self.nodes_status]

    def _parse_vagrant(self, raw: str) -> Dict[str, List[Tuple[str, str]]]:

        result: Dict[str, List[Tuple[str, str]]] = {}
        lines = raw.splitlines()

        for line in lines:
            fields = line.split(",")
            entry: Tuple[str, str] = (fields[1], fields[3])
            state: str = fields[2]
            if state not in result:
                result[state] = []
            result[state].append(entry)

        return result

    def _run(self, cmd: str, interactive: bool = False) -> Tuple[int, str, str]:
        with self.safeenv() as env:
            capture: Optional[int] = subprocess.PIPE
            if interactive:
                capture = None
            proc = subprocess.run(
                shlex.split(cmd),
                stderr=capture,
                stdout=capture,
                env=env
            )
            stdout = "" if interactive else proc.stdout.decode("utf-8")
            stderr = "" if interactive else proc.stderr.decode("utf-8")
            return proc.returncode, stdout, stderr


@contextmanager
def deployment(path: Optional[Path]):

    try:
        target = path if path else Path.cwd()
        vagrantfile = target.joinpath("Vagrantfile")
        if not vagrantfile.exists():
            raise DeploymentNotFinishedError(
                "Deployment not finished; should recreate",
                errno=errno.EINVAL
            )
        yield Vagrant(path)
    finally:
        pass
