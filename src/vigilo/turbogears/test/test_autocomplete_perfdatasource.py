# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.models.demo import functions
import utils

class TestAutocompleterForPerfDataSource(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForPerfDataSource, self).setUp()
        self.host = functions.add_host(u'a.b.c')
        functions.add_vigiloserver(u'localhost')
        functions.add_application(u'vigirrd')
        functions.add_perfdatasource(u'foobarbaz', self.host)

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.perfdatasource(pattern, self.host.name, partial, 42)
