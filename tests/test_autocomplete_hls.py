# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :

import unittest

import tg
from webob import Request
from paste.registry import Registry

from vigilo.models.session import DBSession, metadata
from vigilo.models import tables

from vigilo.turbogears.controllers.autocomplete import AutoCompleteController


class TestAutocompleterForHLS(unittest.TestCase):
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

    def test_no_such_hls(self):
        """Autocomplétion sur un nom de HLS inexistant."""
        # Aucun HLS dans la base ne porte ce nom,
        # dont le résultat doit être vide.
        res = self.ctrl.hls(u'no_such_hls')
        expected = {
            'results': [],
        }
        self.assertEqual(res, expected)

    def test_exact_hls(self):
        """Autocomplétion avec un motif de HLS sans jokers."""
        DBSession.add(tables.HighLevelService(
            servicename=u'foobarbaz',
            message=u'',
            warning_threshold=0,
            critical_threshold=0,
            priority=0,
            op_dep=u'+',
        ))
        DBSession.flush()

        # On doit obtenir le HLS demandé.
        res = self.ctrl.hls(u'foobarbaz')
        expected = {
            'results': [u'foobarbaz'],
        }
        self.assertEqual(res, expected)

    def test_hls_joker_1(self):
        """Autocomplétion sur un motif de HLS avec point d'interrogation."""
        DBSession.add(tables.HighLevelService(
            servicename=u'foobarbaz',
            message=u'',
            warning_threshold=0,
            critical_threshold=0,
            priority=0,
            op_dep=u'+',
        ))
        DBSession.flush()

        # On doit obtenir le HLS "foobarbaz" qui correspond au motif donné.
        res = self.ctrl.hls(u'f?ob?rb?z')
        expected = {
            'results': [u'foobarbaz'],
        }
        self.assertEqual(res, expected)

    def test_hls_joker_n(self):
        """Autocomplétion sur un motif de HLS avec astérisque."""
        DBSession.add(tables.HighLevelService(
            servicename=u'foobarbaz',
            message=u'',
            warning_threshold=0,
            critical_threshold=0,
            priority=0,
            op_dep=u'+',
        ))
        DBSession.flush()

        # On doit obtenir le HLS "foobarbaz" qui correspond au motif donné.
        res = self.ctrl.hls(u'foo*baz')
        expected = {
            'results': [u'foobarbaz'],
        }
        self.assertEqual(res, expected)

    def test_exact_hls_no_access(self):
        """Autocomplétion sur un nom de HLS, sans les permissions."""
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

        DBSession.add(tables.HighLevelService(
            servicename=u'foobarbaz',
            message=u'',
            warning_threshold=0,
            critical_threshold=0,
            priority=0,
            op_dep=u'+',
        ))
        DBSession.flush()

        # On NE doit PAS obtenir le HLS demandé car nous n'avons
        # pas les permissions dessus.
        res = self.ctrl.hls(u'foobarbaz')
        expected = {
            'results': [],
        }
        self.assertEqual(res, expected)

