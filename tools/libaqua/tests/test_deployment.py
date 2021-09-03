# project aquarium's testing battery
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

from datetime import datetime as dt
from unittest.mock import patch
from unittest import TestCase

import libaqua.deployment
from libaqua.errors import AqrError

from libaqua.deployment import (
        LibvirtDeploymentModel,
        VagrantDeploymentModel,
        Deployment)

class TestDeployment(TestCase):

    def test_get_models(self):
        models = list(Deployment.get_models())
        assert 'VagrantDeploymentModel' in models
        assert 'LibvirtDeploymentModel' in models
        assert 'DeploymentModel' not in models

    def test_parse_obj(self):
        _dt_now = dt.now()
        libvirt_model = Deployment._parse_obj(
            dict(model='Libvirt', name='foo', created_on=_dt_now))
        assert type(libvirt_model) == LibvirtDeploymentModel
        vagrant_model = Deployment._parse_obj(
            dict(model='Vagrant', name='foo', created_on=_dt_now, box='foo'))
        assert type(vagrant_model) == VagrantDeploymentModel

        self.assertRaisesRegex(AqrError, 'Unknown deployment',
            Deployment._parse_obj,
                dict(model='Missing', name='foo', created_on=_dt_now, box='foo'))

    def test_get_classes(self):
        classes = list(Deployment.get_classes())
        print(f'Found classes: {classes}')
        assert 'LibvirtDeployment' in classes
        assert 'VagrantDeployment' in classes

    def test_model(self):
        model = LibvirtDeploymentModel(name='foo', created_on=dt.now())
        assert model.name == 'foo'
        assert model.model == 'Libvirt'

