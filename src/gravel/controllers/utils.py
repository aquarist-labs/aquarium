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


from pathlib import Path
from typing import Type, TypeVar
from pydantic import BaseModel
from pydantic.tools import parse_file_as


def _get_file_path(dirpath: Path, name: str) -> Path:
    if not dirpath.exists() or not dirpath.is_dir():
        raise NotADirectoryError()

    file: Path = dirpath.joinpath(f"{name}.json")
    return file


T = TypeVar('T')


def read_model(
    dirpath: Path,
    name: str,
    model: Type[T]
) -> T:
    file: Path = _get_file_path(dirpath, name)
    if not file.exists():
        raise FileNotFoundError()
    elif not file.is_file():
        raise FileExistsError()
    return parse_file_as(model, file)


def write_model(
    dirpath: Path,
    name: str,
    model: BaseModel
):
    file: Path = _get_file_path(dirpath, name)
    if file.exists() and not file.is_file():
        raise FileExistsError()
    file.write_text(model.json())
