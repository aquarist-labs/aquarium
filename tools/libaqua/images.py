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
import logging
import os

from pathlib import Path
from typing import List, Optional, Tuple

from libaqua.misc import find_root
from libaqua.vagrant import Vagrant
from libaqua.errors import (
    BoxAlreadyExistsError,
    ImageNotFoundError,
    VagrantError,
    AqrError
)

logger: logging.Logger = logging.getLogger("aquarium")

def find_images_path() -> Path:
    rootdir = find_root()
    images: Path = rootdir.joinpath(".aqua/images")
    if images.exists():
        return images
    else:
        raise AqrError(f"Images directory [{images}] does not exist")

class Image:
    _name: str
    _path: Path
    _provider: str

    def __init__(self, name: str, path: Path, provider: str) -> None:
        self._name = name
        self._path = path
        self._provider = provider
        pass

    @classmethod
    def list(cls, buildspath: Path) -> List[Image]:
        """
        Return image list if present in the build output directory.
        """
        logger.debug(f'Looking for images in build path: {buildspath}')
        if not buildspath.exists():
            return []

        images: List[Image] = []
        for build in next(os.walk(buildspath))[1]:
            if build.startswith("."):
                continue
            path = buildspath.joinpath(build)
            assert path.exists()
            vagrant_image = cls.find_vagrant_image(name=build, path=path)
            if vagrant_image:
                images.append(vagrant_image)
                continue
            install_image = cls.find_install_image(name=build, path=path)
            if install_image:
                images.append(install_image)

        return images

    @classmethod
    def find_vagrant_image(cls, name: str, path: Path) -> Image:
        logger.debug(f'Looking for vagrant box in "{path}"')
        try:
            provider, imgpath = cls._get_vagrant_image(path)
        except FileNotFoundError:
            return
        assert provider
        assert imgpath

        return Image(name, imgpath, provider)

    @classmethod
    def find_install_image(cls, name: str, path: Path) -> Image:
        logger.debug(f'Looking for install image by the directory: {path}')
        try:
            provider, imgpath = cls._get_install_image(path)
        except FileNotFoundError:
            return
        assert provider
        assert imgpath

        return Image(name, imgpath, provider)

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
            Vagrant.box_add(name, imgpath, imgtype)
        except BoxAlreadyExistsError as e:
            raise e  # just being explicit about what we might propagate
        except VagrantError as e:
            raise e

        return Image(name, imgpath, imgtype)

    @classmethod
    def _get_install_image(cls, path: Path) -> Tuple[str, Path]:
        """
        Return install image provider and path if present below the `path`,
        otherwise raises FileNotFoundError.

        Possible values for image provider: 'unknown', 'libvirt', 'virtualbox'.
        """
        assert path.exists()
        outdir = path.joinpath("_out")
        if not outdir.exists():
            raise FileNotFoundError()

        # we are searching for vagrant box image file
        _name = next((_ for _ in next(os.walk(outdir))[2]
                                if _.startswith('project-aquarium') and
                                   _.endswith('.install.iso')), None)
        if _name:
            _provider = 'any'
            return _provider, outdir.joinpath(_name)
        else:
            raise FileNotFoundError()

    @classmethod
    def _get_vagrant_image(cls, path: Path) -> Tuple[str, Path]:
        """
        Return vagrant image provider and path if present below the `path`,
        otherwise raises FileNotFoundError.

        Possible values for image provider: 'unknown', 'libvirt', 'virtualbox'.
        """
        assert path.exists()
        outdir = path.joinpath("_out")
        if not outdir.exists():
            raise FileNotFoundError()

        _provider = 'unknown'
        # we are searching for vagrant box image file
        _name = next((_ for _ in next(os.walk(outdir))[2]
                                if _.startswith('project-aquarium') and
                                   _.endswith('.box') and
                                   'vagrant' in _), None)
        if _name:
            if 'libvirt' in _name:
                _provider = 'libvirt'
            elif 'virtualbox' in _name:
                _provider = 'virtualbox'
            return _provider, outdir.joinpath(_name)
        else:
            raise FileNotFoundError()

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> Path:
        return self._path

    @property
    def provider(self) -> str:
        return self._provider
