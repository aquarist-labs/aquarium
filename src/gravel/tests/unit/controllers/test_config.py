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
import os
from pathlib import Path

from pyfakefs import fake_filesystem  # pyright: reportMissingTypeStubs=false

from gravel.controllers.config import Config


def test_config_version(fs: fake_filesystem.FakeFilesystem):
    config = Config()
    config.init()
    assert config.config.version == 1


def test_config_options(fs: fake_filesystem.FakeFilesystem):
    config = Config()
    config.init()
    opts = config.options
    assert opts.inventory.probe_interval == 60
    assert opts.storage.probe_interval == 30.0


def test_config_path(fs: fake_filesystem.FakeFilesystem):
    config = Config()
    config.init()
    assert config.confpath == Path("/etc/aquarium/config.json")

    config = Config(path="foo")
    config.init()
    assert config.confpath == Path("foo/config.json")


def test_custom_registry(fs: fake_filesystem.FakeFilesystem) -> None:
    os.environ["AQUARIUM_REGISTRY_URL"] = "foobar"
    os.environ["AQUARIUM_REGISTRY_IMAGE"] = "bar"
    os.environ["AQUARIUM_REGISTRY_SECURE"] = "false"

    config = Config()
    config.init()
    assert config.options.containers.registry == "foobar"
    assert config.options.containers.image == "bar"
    assert not config.options.containers.secure
