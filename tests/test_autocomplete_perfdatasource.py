# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :

import unittest

import tg
from webob import Request
from paste.registry import Registry

from vigilo.models.session import DBSession, metadata
from vigilo.models import tables

from vigilo.turbogears.controllers.autocomplete import AutoCompleteController

class TestAutocompleterForPerfDataSource(unittest.TestCase):
    def setUp(self):
        print "Creating the tables"
        metadata.create_all()

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

        self.host = tables.Host(
            name=u'a.b.c',
            checkhostcmd=u'foo',
            hosttpl=u'bar',
            mainip=u'127.0.0.1',
            snmpcommunity=u'',
            snmpport=4242,
            weight=0,
        )
        DBSession.add(self.host)

        self.ds = tables.PerfDataSource(
            name=u'foobarbaz',
            host=self.host,
            type=u'',
            factor=1.0,
        )
        DBSession.add(self.ds)
        DBSession.flush()

    def tearDown(self):
        print "Dropping all tables"
        DBSession.expunge_all()
        metadata.drop_all()
        self.ctrl = None

    def test_no_such_datasource(self):
        """Autocomplétion sur un nom de datasource inexistant."""
        # Aucune datasource dans la base ne porte ce nom,
        # dont le résultat doit être vide.
        res = self._query_autocompleter(u'no_such_datasource')
        expected = {
            'results': [],
        }
        self.assertEqual(res, expected)

    def test_exact_datasource(self):
        """Autocomplétion avec un motif de datasource sans jokers."""
        # On doit obtenir la datasource demandée.
        res = self._query_autocompleter(u'foobarbaz')
        expected = {'results': [u'foobarbaz']}
        self.assertEqual(res, expected)

    def test_datasource_joker_1(self):
        """Autocomplétion sur une datasource avec point d'interrogation."""
        # On doit obtenir la datasource "foobarbaz"
        # qui correspond au motif donné.
        res = self._query_autocompleter(u'f?ob?rb?z')
        expected = {'results': [u'foobarbaz']}
        self.assertEqual(res, expected)

    def test_datasource_joker_n(self):
        """Autocomplétion sur une datasource avec astérisque."""
        # On doit obtenir la datasource "foobarbaz"
        # qui correspond au motif donné.
        res = self._query_autocompleter(u'foo*baz')
        expected = {'results': [u'foobarbaz']}
        self.assertEqual(res, expected)

    def test_exact_datasource_no_access(self):
        """Autocomplétion sur une datasource, sans les permissions."""
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

        # On NE doit PAS obtenir le datasource demandé car nous n'avons
        # pas les permissions dessus.
        res = self._query_autocompleter(u'*')
        expected = {'results': []}
        self.assertEqual(res, expected)

    def _query_autocompleter(self, pattern):
        return self.ctrl.perfdatasource(pattern, self.host.name)

