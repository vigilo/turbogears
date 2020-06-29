# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.models.demo import functions
from vigilo.turbogears.test import TestController
from .utils import AutoCompleterTest

class TestAutocompleterForSupItemGroup(AutoCompleterTest, TestController):
    def setUp(self):
        TestController.setUp(self)
        AutoCompleterTest.setUp(self)

    def create_deps(self):
        # Le groupe "foobarbaz" est un descendant du groupe "Parent".
        parent = functions.add_supitemgroup(u'Parent')
        child = functions.add_supitemgroup(u'foobarbaz', parent)

        # Positionnement des permissions.
        functions.add_supitemgrouppermission(parent, u'indirect')
        functions.add_supitemgrouppermission(child, u'direct')

    def test_with_or_without_wildcards(self):
        """Autocomplétion sur nom d'élément avec ou sans jokers."""
        for username, group in self.accounts:
            self._change_user(username)
            if username in (u'manager', u'direct', u'indirect'):
                # Ces utilisateurs doivent voir l'élément.
                expected = {'results': [u'foobarbaz']}
            else:
                # Les autres ne voient rien.
                expected = {'results': []}

            # Recherche sur le nom exact.
            res = self._query_autocompleter(u'foobarbaz', False)
            self.assertEqual(res, expected,
                u"Nom exact en tant que %s (%r != %r)" %
                (username, expected, res))
            # Recherche en utilisant le joker '?'.
            res = self._query_autocompleter(u'f?ob?rb?z', False)
            self.assertEqual(res, expected,
                u"Joker '?' en tant que %s (%r != %r)" %
                (username, expected, res))
            # Recherche en utilisant le joker '*'.
            res = self._query_autocompleter(u'foo*baz', False)
            self.assertEqual(res, expected,
                u"Joker '*' en tant que %s (%r != %r)" %
                (username, expected, res))

            # Ces utilisateurs doivent voir l'élément et son parent.
            if username in (u'manager', u'indirect'):
                expected['results'].insert(0, u'Parent')
                expected = {'results': [u'Parent', u'foobarbaz']}

            # Recherche en utilisant uniquement le joker '*'.
            res = self._query_autocompleter(u'*', False)
            self.assertEqual(res, expected,
                u"Uniquement '*' en tant que %s (%r != %r)" %
                (username, expected, res))

    def _query_autocompleter(self, pattern, partial):
        return self.app.post(
            '/autocomplete/supitemgroup',
            {
                'supitemgroup': pattern,
                'partial': partial,
                'noCache': 42
            },
            extra_environ=self.extra_environ).json
