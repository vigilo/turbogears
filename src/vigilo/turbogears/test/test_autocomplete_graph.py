# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.models.demo import functions
import utils

class TestAutocompleterForGraph(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForGraph, self).setUp()
        self.host = functions.add_host(u'a.b.c')
        functions.add_vigiloserver(u'localhost')
        functions.add_application(u'vigirrd')
        ds = functions.add_perfdatasource(u'blahbluhbloh', self.host)
        graph = functions.add_graph(u'foobarbaz')
        functions.add_perfdatasource2graph(ds, graph)

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.graph(pattern, self.host.name, partial, 42)
