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
from pyfakefs import fake_filesystem  # pyright: reportMissingTypeStubs=false

from gravel.controllers.config import Config


def test_config_version(fs: fake_filesystem.FakeFilesystem):
    config = Config()
    assert config.config.version == 1


def test_config_options(fs: fake_filesystem.FakeFilesystem):
    opts = Config().options
    assert opts.inventory.probe_interval == 60
    assert opts.storage.probe_interval == 30.0


def test_config_path(fs: fake_filesystem.FakeFilesystem):
    config = Config()
    assert config.confpath == Path("/etc/aquarium/config.json")
    assert config.options.service_state_path == Path(
        "/etc/aquarium/storage.json"
    )

    config = Config(path="foo")
    assert config.confpath == Path("foo/config.json")
    assert config.options.service_state_path == Path("foo/storage.json")

    # dirname(config.json) != dirname(storage.json)
    config = Config(path="bar")
    config.options.service_state_path = Path("baz")
    config._saveConfig(config.config)  # pyright: reportPrivateUsage=false
    config = Config(path="bar")
    assert config.options.service_state_path == Path("baz")
