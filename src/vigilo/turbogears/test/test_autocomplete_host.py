# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :

from vigilo.models.session import DBSession
from vigilo.models import tables

from vigilo.turbogears.controllers.autocomplete import AutoCompleteController
import utils

class TestAutocompleterForHost(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForHost, self).setUp()

        host = tables.Host(
            name=u'foobarbaz',
            hosttpl=u'bar',
            address=u'127.0.0.1',
            snmpcommunity=u'',
            snmpport=4242,
            weight=0,
        )
        DBSession.add(host)
        DBSession.flush()

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.host(pattern, partial, 42)
