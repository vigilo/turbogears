# -*- coding: utf-8 -*-
# Copyright (C) 2011-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.common.conf import settings
settings.load_file('settings_tests.ini')

from vigilo.models.configure import configure_db
configure_db(settings['database'], 'sqlalchemy_')
