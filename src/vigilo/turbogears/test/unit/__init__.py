# -*- coding: utf-8 -*-
# Copyright (C) 2011-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.common.conf import settings
settings.load_file('test.ini')

from vigilo.models.configure import configure_db
configure_db(settings['app:main'], 'sqlalchemy.')
