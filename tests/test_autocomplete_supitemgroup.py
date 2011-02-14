# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :

from vigilo.models.session import DBSession
from vigilo.models import tables

from vigilo.turbogears.controllers.autocomplete import AutoCompleteController
import utils

class TestAutocompleterForSupItemGroup(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForSupItemGroup, self).setUp()
        DBSession.add(tables.SupItemGroup(name=u'foobarbaz'))
        DBSession.flush()

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.supitemgroup(pattern, partial, 42)
