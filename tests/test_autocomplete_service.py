# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :

from vigilo.models.session import DBSession
from vigilo.models import tables

from vigilo.turbogears.controllers.autocomplete import AutoCompleteController
import utils

class TestAutocompleterForServiceWithoutHost(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForServiceWithoutHost, self).setUp()

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

        self.service = tables.LowLevelService(
            servicename=u'foobarbaz',
            host=self.host,
            command=u'',
            weight=42,
        )
        DBSession.add(self.service)
        DBSession.flush()

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
