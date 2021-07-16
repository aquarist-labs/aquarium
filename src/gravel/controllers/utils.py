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

import asyncio
import random
import string
from logging import Logger
from pathlib import Path
from typing import List, Optional, Tuple, Type, TypeVar
from pydantic import BaseModel
from pydantic.tools import parse_file_as
from fastapi.logger import logger as fastapi_logger


logger: Logger = fastapi_logger


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
