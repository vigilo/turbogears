# -*- coding: utf-8 -*-

import unittest
import tg
from webob import Request
from paste.registry import Registry

from vigilo.turbogears.controllers.autocomplete import AutoCompleteController
from vigilo.models.session import metadata, DBSession
from vigilo.models import tables

class DbTest(unittest.TestCase):
    def setUp(self):
        print "Creating the tables"
        metadata.create_all()
        DBSession.add(tables.StateName(statename=u'OK', order=1))
        DBSession.add(tables.StateName(statename=u'UNKNOWN', order=2))
        DBSession.add(tables.StateName(statename=u'WARNING', order=3))
        DBSession.add(tables.StateName(statename=u'CRITICAL', order=4))
        DBSession.add(tables.StateName(statename=u'UP', order=1))
        DBSession.add(tables.StateName(statename=u'UNREACHABLE', order=2))
        DBSession.add(tables.StateName(statename=u'DOWN', order=4))
        DBSession.flush()

    def tearDown(self):
        DBSession.expunge_all()
        print "Dropping all tables"
        metadata.drop_all()

class AutoCompleterTest(DbTest):
    def setUp(self):
        super(AutoCompleterTest, self).setUp()
        environ = {
            'repoze.what.credentials': {
                'groups': ['managers'],
            }
        }
        request = Request(environ)
        registry = Registry()
        registry.prepare()
        registry.register(tg.request, request)
        self.ctrl = AutoCompleteController()

        tg.request.identity = {
            'repoze.who.userid': 'manager',
        }

        manager = tables.User(
            user_name=u'manager',
            fullname=u'',
            email=u'manager@test',
        )
        DBSession.add(manager)

        managers = tables.UserGroup(
            group_name=u'managers',
        )
        DBSession.add(managers)
        manager.usergroups.append(managers)

    def tearDown(self):
        self.ctrl
        super(AutoCompleterTest, self).tearDown()

    def shortDescription(self):
        desc = DbTest.shortDescription(self)
        return "%s (%s)" % (desc, self.__class__.__name__)

    def run(self, result):
        if self.__class__ == AutoCompleterTest:
            return
        return super(AutoCompleterTest, self).run(result)

    def test_no_such_item(self):
        """Autocomplétion sur un élément inexistant."""
        # Aucun élément dans la base ne porte ce nom,
        # dont le résultat doit être vide.
        res = self._query_autocompleter(u'no_such_graph', False)
        expected = {'results': []}
        self.assertEqual(res, expected)

    def test_no_such_item_partial(self):
        """Autocomplétion sur un élément inexistant (partial)."""
        # Aucun élément dans la base ne porte ce nom,
        # dont le résultat doit être vide.
        res = self._query_autocompleter(u'no_such_graph', True)
        expected = {'results': []}
        self.assertEqual(res, expected)

    def test_exact_item_name(self):
        """Autocomplétion avec un nom d'élément sans jokers."""
        # On doit obtenir l'élément demandé.
        res = self._query_autocompleter('foobarbaz', False)
        expected = {'results': ['foobarbaz']}
        self.assertEqual(res, expected)

    def test_joker_1(self):
        """Autocomplétion sur un nom d'élément avec point d'interrogation."""
        # On doit obtenir l'élément "foobarbaz"
        # qui correspond au motif donné.
        res = self._query_autocompleter(u'f?ob?rb?z', False)
        expected = {'results': [u'foobarbaz']}
        self.assertEqual(res, expected)

    def test_joker_n(self):
        """Autocomplétion sur un nom d'élément avec astérisque."""
        # On doit obtenir l'élément "foobarbaz"
        # qui correspond au motif donné.
        res = self._query_autocompleter(u'foo*baz', False)
        expected = {'results': [u'foobarbaz']}
        self.assertEqual(res, expected)

    def test_without_access(self):
        """Autocomplétion sur un nom d'élément, sans les permissions."""
        DBSession.add(tables.User(
            user_name=u'foobar',
            fullname=u'',
            email=u'foobar@test',
        ))

        # On simulte un utilisateur connecté sous l'identifiant "foobar".
        tg.request.identity = {
            'repoze.who.userid': 'foobar',
        }
        tg.request.environ['repoze.what.credentials']['groups'] = []

        # On NE doit PAS obtenir l'élément demandé car nous n'avons
        # pas les permissions dessus.
        res = self._query_autocompleter(u'foobarbaz', False)
        expected = {'results': []}
        self.assertEqual(res, expected)

        res = self._query_autocompleter(u'*', False)
        expected = {'results': []}
        self.assertEqual(res, expected)

    def test_partial(self):
        """Autocomplétion sur un nom d'élément partiel."""
        # La correspondance partielle ne se fait qu'en fin de nom.
        res = self._query_autocompleter(u'foobar', True)
        expected = {'results': [u'foobarbaz']}
        self.assertEqual(res, expected)

        res = self._query_autocompleter(u'bar', True)
        expected = {'results': []}
        self.assertEqual(res, expected)

        res = self._query_autocompleter(u'barbaz', True)
        expected = {'results': []}
        self.assertEqual(res, expected)

