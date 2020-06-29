# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import transaction
from vigilo.models.demo import functions
from vigilo.models.session import DBSession

class AutoCompleterTest(object):
    check_permissions = True

    # Les caractères "_" & "%" sont spéciaux en SQL.
    # Leur usage permet de détecter les échappements abusifs (#943).
    hostname = u'a.b.c_d%e'

    def setUp(self):
        self.extra_environ = {}
        self.accounts = (
            ('nobody', 'nobody'),       # Accès à rien.
            ('direct', 'direct'),       # Permissions directe sur l'objet.
            ('indirect', 'indirect'),   # Permissions indirectes sur l'objet.
        )

        # Création des comptes utilisateurs.
        for username, group in self.accounts:
            functions.add_user(unicode(username), u'%s@test' % username,
                               u'', u'', unicode(group))
        DBSession.flush()

        # Création de l'arborescence des objets.
        self.create_deps()
        DBSession.flush()
        transaction.commit()

    def shortDescription(self):
        # Repris du code de unittest
        doc = self._testMethodDoc
        if doc:
            return "%s: %s" % (self.__class__.__name__,
                               doc.split("\n")[0].strip())
        return None

    def _change_user(self, user):
        self.extra_environ['REMOTE_USER'] = user

    def test_no_such_item(self):
        """Autocomplétion sur un élément inexistant."""
        # L'élément n'existe pas : on attend une liste de résultats vide.
        expected = {'results': []}
        for username, group in self.accounts:
            self._change_user(username)

            # On teste une première fois en effectuant une recherche exacte.
            res = self._query_autocompleter(u'no_such_graph', False)
            self.assertEqual(res, expected,
                u"Element inexistant/recherche exacte pour %s (%r != %r)" %
                (username, expected, res))

            # Puis une seconde fois avec une recherche partielle.
            res = self._query_autocompleter(u'no_such_graph', True)
            self.assertEqual(res, expected,
                u"Element inexistant/recherche partielle pour %s (%r != %r)" %
                (username, expected, res))

    def test_with_or_without_wildcards(self):
        """Autocomplétion sur nom d'élément avec ou sans jokers."""
        for username, group in self.accounts:
            self._change_user(username)
            if (not self.check_permissions) or \
                username in (u'manager', u'direct', u'indirect'):
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

            # Recherche en utilisant uniquement le joker '*'.
            res = self._query_autocompleter(u'*', False)
            self.assertEqual(res, expected,
                u"Uniquement '*' en tant que %s (%r != %r)" %
                (username, expected, res))

    def test_partial(self):
        """Autocomplétion sur un nom d'élément en recherche partielle."""
        for username, group in self.accounts:
            self._change_user(username)
            if (not self.check_permissions) or \
                username in (u'manager', u'direct', u'indirect'):
                # Ces utilisateurs doivent voir l'élément.
                expected = {'results': [u'foobarbaz']}
            else:
                # Les autres ne voient rien.
                expected = {'results': []}

            # La correspondance partielle se fait par rapport à un préfixe.
            res = self._query_autocompleter(u'foobar', True)
            self.assertEqual(res, expected,
                u"Recherche partielle avec prefixe en tant que %s (%r != %r)" %
                (username, expected, res))
            expected = {'results': []}
            res = self._query_autocompleter(u'bar', True)
            self.assertEqual(res, expected,
                u"Recherche partielle avec infixe en tant que %s (%r != %r)" %
                (username, expected, res))
            res = self._query_autocompleter(u'barbaz', True)
            self.assertEqual(res, expected,
                u"Recherche partielle avec suffixe en tant que %s (%r != %r)" %
                (username, expected, res))
