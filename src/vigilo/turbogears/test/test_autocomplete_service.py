# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.models.demo import functions
import utils

class TestAutocompleterForServiceWithoutHost(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForServiceWithoutHost, self).setUp()
        self.host = functions.add_host(u'a.b.c')
        self.service = functions.add_lowlevelservice(self.host, u'foobarbaz')

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.service(pattern, None, partial, 42)

class TestAutocompleterForServiceWithHost(
    TestAutocompleterForServiceWithoutHost):

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.service(pattern, self.host.name, partial, 42)

# @TODO: ajouter d'autres tests...
# Exemples de tests possibles:
# - un autre hôte avec un service du même nom
#   (test du DISTINCT sur les résultats)
# - un autre service répondant au motif, avec et sans hôte
#   (vérif de la bonne prise en compte du nom d'hôte)
# - etc.
