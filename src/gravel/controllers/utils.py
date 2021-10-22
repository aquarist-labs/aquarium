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

from __future__ import annotations

import asyncio
import random
import string
from logging import Logger
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union

from fastapi.logger import logger as fastapi_logger
from pydantic import BaseModel, root_validator
from pydantic.tools import parse_file_as

logger: Logger = fastapi_logger


class HWEntryModel(BaseModel):
    id: str
    cls: str
    claimed: Optional[bool]
    product: Optional[str]
    vendor: Optional[str]
    logicalname: Optional[Union[str, List[str]]]
    configuration: Optional[Dict[str, Any]]
    capabilities: Optional[Dict[str, Any]]
    size: Optional[int]
    units: Optional[str]
    capacity: Optional[int]
    children: Optional[List[HWEntryModel]]

    @root_validator(pre=True)
    def class_to_cls(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "class" in values:
            values["cls"] = values["class"]
            del values["class"]
        return values


# ensure pydantic updates forward references, because we're using a
# self-referencing model.
HWEntryModel.update_forward_refs()


def _get_file_path(dirpath: Path, name: str) -> Path:
    if not dirpath.exists() or not dirpath.is_dir():
        raise NotADirectoryError()

    file: Path = dirpath.joinpath(f"{name}.json")
    return file


T = TypeVar("T")


def read_model(dirpath: Path, name: str, model: Type[T]) -> T:
    file: Path = _get_file_path(dirpath, name)
    if not file.exists():
        raise FileNotFoundError()
    elif not file.is_file():
        raise FileExistsError()
    return parse_file_as(model, file)


def write_model(dirpath: Path, name: str, model: BaseModel):
    file: Path = _get_file_path(dirpath, name)
    if file.exists() and not file.is_file():
        raise FileExistsError()
    file.write_text(model.json())


async def aqr_run_cmd(
    args: List[str],
) -> Tuple[int, Optional[str], Optional[str]]:

    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout: Optional[str] = None
    stderr: Optional[str] = None

    if proc.stdout:
        stdout = (await proc.stdout.read()).decode("utf-8")
    if proc.stderr:
        stderr = (await proc.stderr.readline()).decode("utf-8")

    retcode = await asyncio.wait_for(proc.wait(), None)
    logger.debug(f"run {args}: retcode = {proc.returncode}")

    return retcode, stdout, stderr


def random_string(length: int) -> str:
    """
    Return a random text string containing printable characters.
    :param length: The length of the string.
    :return: Returns a random string.
    """
    return "".join(random.choices(string.printable, k=length))


async def lshw() -> HWEntryModel:
    cmd = ["lshw", "-json"]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    assert process.stdout
    assert process.stderr

    retcode = await asyncio.wait_for(process.wait(), None)
    assert retcode == 0
    out = await process.stdout.read()
    outstr = out.decode("utf-8")
    return HWEntryModel.parse_raw(outstr)
