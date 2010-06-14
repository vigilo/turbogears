# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :

import unittest

import tg
from webob import Request
from paste.registry import Registry

from vigilo.models.session import DBSession, metadata
from vigilo.models import tables

from vigilo.turbogears.controllers.autocomplete import AutoCompleteController


class TestAutocompleterForHost(unittest.TestCase):
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

        DBSession.add(tables.Host(
            name=u'a.b.c',
            checkhostcmd=u'foo',
            hosttpl=u'bar',
            mainip=u'127.0.0.1',
            snmpcommunity=u'',
            snmpport=4242,
            weight=0,
        ))
        DBSession.flush()

    def tearDown(self):
        print "Dropping all tables"
        DBSession.expunge_all()
        metadata.drop_all()
        self.ctrl = None

    def test_no_such_host(self):
        """Autocomplétion sur un nom d'hôte inexistant."""
        # Aucun hôte dans la base ne porte ce nom,
        # dont le résultat doit être vide.
        res = self.ctrl.host(u'no_such_host')
        expected = {'results': []}
        self.assertEqual(res, expected)

    def test_exact_host(self):
        """Autocomplétion avec un motif d'hôte sans jokers."""
        # On doit obtenir l'hôte demandé.
        res = self.ctrl.host(u'a.b.c')
        expected = {'results': [u'a.b.c']}
        self.assertEqual(res, expected)

    def test_host_joker_1(self):
        """Autocomplétion sur un motif d'hôte avec point d'interrogation."""
        # On doit obtenir l'hôte "a.b.c" qui correspond au motif donné.
        res = self.ctrl.host(u'a.?.c')
        expected = {'results': [u'a.b.c']}
        self.assertEqual(res, expected)

    def test_host_joker_n(self):
        """Autocomplétion sur un motif d'hôte avec astérisque."""
        # On doit obtenir l'hôte "a.b.c" qui correspond au motif donné.
        res = self.ctrl.host(u'a*c')
        expected = {'results': [u'a.b.c']}
        self.assertEqual(res, expected)

    def test_exact_host_no_access(self):
        """Autocomplétion sur un motif d'hôte, sans les permissions."""
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

        # On NE doit PAS obtenir l'hôte demandé car nous n'avons
        # pas les permissions dessus.
        res = self.ctrl.host(u'a*c')
        expected = {'results': []}
        self.assertEqual(res, expected)

