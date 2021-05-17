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
import errno
import os
from pathlib import Path
from typing import List, Optional, Tuple

from libaqr.vagrant import Vagrant
from libaqr.errors import (
    BoxAlreadyExistsError,
    ImageNotFoundError,
    VagrantError
)


class Image:
    _name: str
    _path: Path
    _type: str

    def __init__(self, name: str, path: Path, type: str) -> None:
        self._name = name
        self._path = path
        self._type = type
        pass

    @classmethod
    def list(cls, buildspath: Path) -> List[Image]:

        if not buildspath.exists():
            return []

        images: List[Image] = []
        for build in next(os.walk(buildspath))[1]:
            if build.startswith("."):
                continue

            path = buildspath.joinpath(build)
            assert path.exists()
            try:
                type, imgpath = cls._get_vagrant_image(path)
            except FileNotFoundError:
                continue
            assert type
            assert imgpath

            images.append(Image(build, imgpath, type))

        return images

    @classmethod
    def add(cls, buildpath: Path, name: str) -> Image:

        imgbuild = buildpath.joinpath(name)
        if not imgbuild.exists():
            raise ImageNotFoundError(
                msg="image build not found",
                errno=errno.ENOENT
            )

        try:
            imgtype, imgpath = cls._get_vagrant_image(imgbuild)
        except FileNotFoundError:
            raise ImageNotFoundError(
                msg="image not built",
                errno=errno.EINVAL
            )
        assert imgpath.exists()

        try:
            Vagrant.box_add(name, imgpath)
        except BoxAlreadyExistsError as e:
            raise e  # just being explicit about what we might propagate
        except VagrantError as e:
            raise e

        return Image(name, imgpath, imgtype)

    @classmethod
    def _get_vagrant_image(cls, path: Path) -> Tuple[str, Path]:
        """
        Return vagrant image type and path if present below the `path`,
        otherwise raises FileNotFoundError.

        Possible values for image type: 'unknown', 'libvirt'.
        """
        assert path.exists()
        outdir = path.joinpath("_out")
        if not outdir.exists():
            raise FileNotFoundError()

        _type = 'unknown'
        # we are searching for vagrant box image file
        _name = next((_ for _ in next(os.walk(outdir))[2]
                                if _.startswith('project-aquarium') and
                                   _.endswith('.box') and
                                   'vagrant' in _), None)
        if _name:
            if 'libvirt' in _name:
                _type = 'libvirt'
            return _type, outdir.joinpath(_name)
        else:
            raise FileNotFoundError()

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> Path:
        return self._path

    @property
    def type(self) -> str:
        return self._type
