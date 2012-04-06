# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import nose
from vigilo.models.demo import functions
import utils

class TestAutocompleterForHLS(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForHLS, self).setUp()
        hls = functions.add_highlevelservice(u'foobarbaz')

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.hls(pattern, partial, 42)

    def test_without_access(self):
        raise nose.plugins.skip.SkipTest("Not ready yet.")
