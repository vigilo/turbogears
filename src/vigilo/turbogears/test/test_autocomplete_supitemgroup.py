# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :

from vigilo.models.demo import functions
import utils

class TestAutocompleterForSupItemGroup(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForSupItemGroup, self).setUp()
        functions.add_supitemgroup(u'foobarbaz')

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.supitemgroup(pattern, partial, 42)
