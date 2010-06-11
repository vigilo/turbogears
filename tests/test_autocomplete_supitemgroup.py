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
        DBSession.flush()

    def tearDown(self):
        print "Dropping all tables"
        DBSession.expunge_all()
        metadata.drop_all()
        self.ctrl = None

    def test_no_such_supitemgroup(self):
        """Autocomplétion sur un nom de supitemgroup inexistant."""
        # Aucun SupItemGroup dans la base ne porte ce nom,
        # dont le résultat doit être vide.
        res = self.ctrl.supitemgroup(u'no_such_supitemgroup')
        expected = {
            'results': [],
        }
        self.assertEqual(res, expected)

    def test_exact_supitemgroup(self):
        """Autocomplétion avec un motif de supitemgroup sans jokers."""
        DBSession.add(tables.SupItemGroup(
            name=u'foobarbaz',
        ))
        DBSession.flush()

        # On doit obtenir le supitemgroup demandé.
        res = self.ctrl.supitemgroup(u'foobarbaz')
        expected = {
            'results': [u'foobarbaz'],
        }
        self.assertEqual(res, expected)

    def test_supitemgroup_joker_1(self):
        """Autocomplétion sur un motif de supitemgroup avec point d'interrogation."""
        DBSession.add(tables.SupItemGroup(
            name=u'foobarbaz',
        ))
        DBSession.flush()

        # On doit obtenir le supitemgroup "foobarbaz"
        # qui correspond au motif donné.
        res = self.ctrl.supitemgroup(u'f?ob?rb?z')
        expected = {
            'results': [u'foobarbaz'],
        }
        self.assertEqual(res, expected)

    def test_supitemgroup_joker_n(self):
        """Autocomplétion sur un motif de supitemgroup avec astérisque."""
        DBSession.add(tables.SupItemGroup(
            name=u'foobarbaz',
        ))
        DBSession.flush()

        # On doit obtenir le supitemgroup "foobarbaz"
        # qui correspond au motif donné.
        res = self.ctrl.supitemgroup(u'foo*baz')
        expected = {
            'results': [u'foobarbaz'],
        }
        self.assertEqual(res, expected)

    def test_exact_supitemgroup_no_access(self):
        """Autocomplétion sur un nom de supitemgroup, sans les permissions."""
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

        DBSession.add(tables.SupItemGroup(
            name=u'foobarbaz',
        ))
        DBSession.flush()

        # On NE doit PAS obtenir le supitemgroup demandé car nous n'avons
        # pas les permissions dessus.
        res = self.ctrl.supitemgroup(u'foobarbaz')
        expected = {
            'results': [],
        }
        self.assertEqual(res, expected)

