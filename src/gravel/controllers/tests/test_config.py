from datetime import datetime
from pathlib import Path
from pyfakefs.fake_filesystem_unittest import TestCase

from gravel.controllers.config \
    import Config, DeploymentStage


class TestConfig(TestCase):

    def setUp(self):
        self.setUpPyfakefs()

    def test_config_version(self):
        config = Config()
        assert config.config.version == 3

    def test_deployment_state(self):
        ds = Config().deployment_state
        assert ds.stage == DeploymentStage.none
        assert ds.last_modified < datetime.now()

    def test_config_path(self):
        config = Config()
        assert config.confpath == Path('/etc/aquarium/config.json')

        config = Config(path='foo')
        assert config.confpath == Path('foo/config.json')
