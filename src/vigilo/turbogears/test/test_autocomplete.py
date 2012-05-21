# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import nose

from vigilo.models.demo import functions
import utils


class TestAutocompleterForPerfDataSource(utils.AutoCompleterTest):
    def create_deps(self):
        # Les caractères "_" & "%" sont spéciaux en SQL.
        # Leur usage permet de détecter les échappements abusifs (#943).
        self.host = functions.add_host(u'a.b.c_d%e')
        functions.add_vigiloserver(u'localhost')
        functions.add_application(u'vigirrd')
        functions.add_perfdatasource(u'foobarbaz', self.host)
        # L'hôte appartient au groupe "Child".
        parent = functions.add_supitemgroup(u'Parent')
        child = functions.add_supitemgroup(u'Child', parent)
        functions.add_host2group(self.host, child)
        # Positionnement des permissions.
        functions.add_supitemgrouppermission(parent, u'indirect')
        functions.add_supitemgrouppermission(child, u'direct')

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.perfdatasource(pattern, self.host.name, partial, 42)


class TestAutocompleterForGraph(utils.AutoCompleterTest):
    def create_deps(self):
        # Les caractères "_" & "%" sont spéciaux en SQL.
        # Leur usage permet de détecter les échappements abusifs (#943).
        self.host = functions.add_host(u'a.b.c_d%e')
        functions.add_vigiloserver(u'localhost')
        functions.add_application(u'vigirrd')
        ds = functions.add_perfdatasource(u'blahbluhbloh', self.host)
        graph = functions.add_graph(u'foobarbaz')
        functions.add_perfdatasource2graph(ds, graph)
        # L'hôte appartient au groupe "Child".
        parent = functions.add_supitemgroup(u'Parent')
        child = functions.add_supitemgroup(u'Child', parent)
        functions.add_host2group(self.host, child)
        # Positionnement des permissions.
        functions.add_supitemgrouppermission(parent, u'indirect')
        functions.add_supitemgrouppermission(child, u'direct')

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.graph(pattern, self.host.name, partial, 42)


class TestAutocompleterForHLS(utils.AutoCompleterTest):
    # L'auto-complétion sur les noms de HLS
    # ne nécessite pas de permissions.
    check_permissions = False

    def create_deps(self):
        hls = functions.add_highlevelservice(u'foobarbaz')
        # Le service appartient au groupe "Child".
        parent = functions.add_supitemgroup(u'Parent')
        child = functions.add_supitemgroup(u'Child', parent)
        functions.add_host2group(hls, child)
        # Positionnement des permissions.
        functions.add_supitemgrouppermission(parent, u'indirect')
        functions.add_supitemgrouppermission(child, u'direct')

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.hls(pattern, partial, 42)

    def test_without_access(self):
        raise nose.plugins.skip.SkipTest("Not ready yet.")


class TestAutocompleterForHost(utils.AutoCompleterTest):
    def create_deps(self):
        host = functions.add_host(u'foobarbaz')
        # L'hôte appartient au groupe "Child".
        parent = functions.add_supitemgroup(u'Parent')
        child = functions.add_supitemgroup(u'Child', parent)
        functions.add_host2group(host, child)
        # Positionnement des permissions.
        functions.add_supitemgrouppermission(parent, u'indirect')
        functions.add_supitemgrouppermission(child, u'direct')

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.host(pattern, partial, 42)


class TestAutocompleterForServiceWithoutHost(utils.AutoCompleterTest):
    def create_deps(self):
        # Les caractères "_" & "%" sont spéciaux en SQL.
        # Leur usage permet de détecter les échappements abusifs (#943).
        self.host = functions.add_host(u'a.b.c_d%e')
        self.service = functions.add_lowlevelservice(self.host, u'foobarbaz')
        # L'hôte appartient au groupe "Child".
        parent = functions.add_supitemgroup(u'Parent')
        child = functions.add_supitemgroup(u'Child', parent)
        functions.add_host2group(self.host, child)
        # Positionnement des permissions.
        functions.add_supitemgrouppermission(parent, u'indirect')
        functions.add_supitemgrouppermission(child, u'direct')

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


class TestAutocompleterForSupItemGroup(utils.AutoCompleterTest):
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
            self._change_user(username, [group])
            if username in (u'manager', u'direct', u'indirect'):
                # Ces utilisateurs doivent voir l'élément.
                expected = {'results': [u'foobarbaz']}
            else:
                # Les autres ne voient rien.
                expected = {'results': []}

            # Recherche sur le nom exact.
            res = self._query_autocompleter(u'foobarbaz', False)
            self.assertEqual(res, expected,
                u"Nom exact en tant que %s" % username)
            # Recherche en utilisant le joker '?'.
            res = self._query_autocompleter(u'f?ob?rb?z', False)
            self.assertEqual(res, expected,
                u"Joker '?' en tant que %s" % username)
            # Recherche en utilisant le joker '*'.
            res = self._query_autocompleter(u'foo*baz', False)
            self.assertEqual(res, expected,
                u"Joker '*' en tant que %s" % username)

            # Ces utilisateurs doivent voir l'élément et son parent.
            if username in (u'manager', u'indirect'):
                expected['results'].insert(0, u'Parent')
                expected = {'results': [u'Parent', u'foobarbaz']}

            # Recherche en utilisant uniquement le joker '*'.
            res = self._query_autocompleter(u'*', False)
            self.assertEqual(res, expected,
                u"Uniquement '*' en tant que %s" % username)

    def _query_autocompleter(self, pattern, partial):
        return self.ctrl.supitemgroup(pattern, partial, 42)
