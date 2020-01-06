# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.models.demo import functions
from vigilo.turbogears.test import TestController
from .utils import AutoCompleterTest

class TestAutocompleterForGraph(AutoCompleterTest, TestController):
    def setUp(self):
        TestController.setUp(self)
        AutoCompleterTest.setUp(self)

    def create_deps(self):
        host = functions.add_host(self.hostname)
        functions.add_vigiloserver(u'localhost')
        functions.add_application(u'vigirrd')
        ds = functions.add_perfdatasource(u'blahbluhbloh', host)
        graph = functions.add_graph(u'foobarbaz')
        functions.add_perfdatasource2graph(ds, graph)

        # L'hôte appartient au groupe "Child".
        parent = functions.add_supitemgroup(u'Parent')
        child = functions.add_supitemgroup(u'Child', parent)
        functions.add_host2group(host, child)

        # Positionnement des permissions.
        functions.add_supitemgrouppermission(parent, u'indirect')
        functions.add_supitemgrouppermission(child, u'direct')

    def _query_autocompleter(self, pattern, partial):
        return self.app.post(
            '/autocomplete/graph',
            {
                'graphname': pattern,
                'host': self.hostname,
                'partial': partial,
                'noCache': 42
            },
            extra_environ=self.extra_environ).json
