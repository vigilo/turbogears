# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :

from vigilo.models.demo import functions
import utils

class TestAutocompleterForHost(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForHost, self).setUp()
        functions.add_host(u'foobarbaz')

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.host(pattern, partial, 42)
