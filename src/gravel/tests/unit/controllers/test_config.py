from pathlib import Path

from gravel.controllers.config import Config


def test_config_version(fs):
    config = Config()
    assert config.config.version == 1


def test_config_options(fs):
    opts = Config().options
    assert opts.inventory.probe_interval == 60
    assert opts.storage.probe_interval == 30.0


def test_config_path(fs):
    config = Config()
    assert config.confpath == Path('/etc/aquarium/config.json')
    assert (config.options.service_state_path ==
            Path('/etc/aquarium/storage.json'))

    config = Config(path='foo')
    assert config.confpath == Path('foo/config.json')
    assert config.options.service_state_path == Path('foo/storage.json')

    # dirname(config.json) != dirname(storage.json)
    config = Config(path='bar')
    config.options.service_state_path = Path('baz')
    config._saveConfig(config.config)
    config = Config(path='bar')
    assert config.options.service_state_path == Path('baz')
