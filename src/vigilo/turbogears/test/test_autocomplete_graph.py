# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.models.session import DBSession
from vigilo.models import tables

import utils

class TestAutocompleterForGraph(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForGraph, self).setUp()

        self.host = tables.Host(
            name=u'a.b.c',
            hosttpl=u'bar',
            address=u'127.0.0.1',
            snmpcommunity=u'',
            snmpport=4242,
            weight=0,
        )
        DBSession.add(self.host)

        ds = tables.PerfDataSource(
            name=u'blahbluhbloh',
            host=self.host,
            type=u'',
            factor=42,
        )
        DBSession.add(ds)

        graph = tables.Graph(
            name=u'foobarbaz',
            template=u'',
            vlabel=u'',
        )
        DBSession.add(graph)
        graph.perfdatasources.append(ds)
        DBSession.flush()

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.graph(pattern, self.host.name, partial, 42)
