# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :

import nose

from vigilo.models.session import DBSession
from vigilo.models import tables

from vigilo.turbogears.controllers.autocomplete import AutoCompleteController
import utils

class TestAutocompleterForHLS(utils.AutoCompleterTest):
    def setUp(self):
        super(TestAutocompleterForHLS, self).setUp()

        hls = tables.HighLevelService(
            servicename=u'foobarbaz',
            message=u'',
            warning_threshold=0,
            critical_threshold=0,
        )
        DBSession.add(hls)
        DBSession.flush()

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.hls(pattern, partial, 42)

    def test_without_access(self):
        raise nose.plugins.skip.SkipTest("Not ready yet.")
