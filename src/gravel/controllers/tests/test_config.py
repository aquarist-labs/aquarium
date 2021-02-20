from datetime import datetime
from pathlib import Path
from pyfakefs.fake_filesystem_unittest \
    import TestCase  # pyright: reportMissingTypeStubs=false

from gravel.controllers.config \
    import Config, DeploymentStage


class TestConfig(TestCase):

    def setUp(self):
        self.setUpPyfakefs()  # type: ignore

    def test_config_version(self):
        config = Config()
        assert config.config.version == 3

    def test_deployment_state(self):
        ds = Config().deployment_state
        assert ds.stage == DeploymentStage.none
        assert ds.last_modified < datetime.now()

    def test_config_options(self):
        opts = Config().options
        assert opts.inventory.probe_interval == 60
        assert opts.storage.probe_interval == 30.0

    def test_config_path(self):
        config = Config()
        assert config.confpath == Path('/etc/aquarium/config.json')
        assert config.options.service_state_path == Path('/etc/aquarium/storage.json')

        config = Config(path='foo')
        assert config.confpath == Path('foo/config.json')
        assert config.options.service_state_path == Path('foo/storage.json')

        # dirname(config.json) != dirname(storage.json)
        config = Config(path='bar')
        config.options.service_state_path = Path('baz')
        config._saveConfig(config.config)
        config = Config(path='bar')
        assert config.options.service_state_path == Path('baz')
