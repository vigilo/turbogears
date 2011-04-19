# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.models.session import DBSession
from vigilo.models import tables

from vigilo.turbogears.controllers.autocomplete import AutoCompleteController
import utils

class TestAutocompleterForPerfDataSource(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForPerfDataSource, self).setUp()

        self.host = tables.Host(
            name=u'a.b.c',
            checkhostcmd=u'foo',
            hosttpl=u'bar',
            address=u'127.0.0.1',
            snmpcommunity=u'',
            snmpport=4242,
            weight=0,
        )
        DBSession.add(self.host)

        ds = tables.PerfDataSource(
            name=u'foobarbaz',
            host=self.host,
            type=u'',
            factor=1.0,
        )
        DBSession.add(ds)
        DBSession.flush()

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.perfdatasource(pattern, self.host.name, partial, 42)
