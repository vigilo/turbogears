# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.models.demo import functions
from vigilo.turbogears.test import TestController
from .utils import AutoCompleterTest

class TestAutocompleterForServiceWithoutHost(AutoCompleterTest, TestController):
    def setUp(self):
        TestController.setUp(self)
        AutoCompleterTest.setUp(self)

    def create_deps(self):
        host = functions.add_host(self.hostname)
        self.service = functions.add_lowlevelservice(host, u'foobarbaz')

        # L'hôte appartient au groupe "Child".
        parent = functions.add_supitemgroup(u'Parent')
        child = functions.add_supitemgroup(u'Child', parent)
        functions.add_host2group(host, child)

        # Positionnement des permissions.
        functions.add_supitemgrouppermission(parent, u'indirect')
        functions.add_supitemgrouppermission(child, u'direct')

    def _query_autocompleter(self, pattern, partial):
        return self.app.post(
            '/autocomplete/service',
            {
                'service': pattern,
                'partial': partial,
                'noCache': 42
            },
            extra_environ=self.extra_environ).json


class TestAutocompleterForServiceWithHost(TestAutocompleterForServiceWithoutHost):
    def _query_autocompleter(self, pattern, partial):
        return self.app.post(
            '/autocomplete/service',
            {
                'service': pattern,
                'host': self.hostname,
                'partial': partial,
                'noCache': 42
            },
            extra_environ=self.extra_environ).json

    # @TODO: ajouter d'autres tests...
    # Exemples de tests possibles:
    # - un autre hôte avec un service du même nom
    #   (test du DISTINCT sur les résultats)
    # - un autre service répondant au motif, avec et sans hôte
    #   (vérif de la bonne prise en compte du nom d'hôte)
    # - etc.
