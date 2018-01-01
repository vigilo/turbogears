# -*- coding: utf-8 -*-
# Copyright (C) 2017-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import sys
from vigilo.turbogears import VigiloAppConfig
from vigilo.turbogears import test_stack
from vigilo.turbogears.test_stack.lib import app_globals, helpers

base_config = VigiloAppConfig('TurboGears')
base_config.package = test_stack
