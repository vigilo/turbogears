# -*- coding: utf-8 -*-
# Copyright (C) 2006-2015 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import os
import shutil
import unittest

import tg
import transaction
from webob import Request
from paste.registry import Registry

import vigilo.turbogears as vigilo_tg
from vigilo.turbogears.app_cfg import VigiloAppConfig
from vigilo.turbogears.controllers.autocomplete import AutoCompleteController
from vigilo.models.demo import functions
from vigilo.models.test.controller import setup_db, teardown_db
from vigilo.models import tables
from vigilo.models.session import DBSession

import pylons
from pylons import url
from tg import tmpl_context
from pylons.util import ContextObj


class DbTest(unittest.TestCase):
    def setUp(self):
        print "Creating the tables"
        setup_db()

    def tearDown(self):
        print "Dropping all tables"
        transaction.abort()
        DBSession.expunge_all()
        teardown_db()

class AutoCompleterTest(DbTest):
    check_permissions = True

    def setUp(self):
        super(AutoCompleterTest, self).setUp()
        # Création d'un environnement WSGI pour les tests.
        # Par défaut, l'utilisateur n'est pas identifé
        # et n'appartient donc à aucun groupe.
        environ = {'repoze.what.credentials': {
                'groups': [],
            }
        }
        request = Request(environ)
        config = VigiloAppConfig('TurboGears')
        config.init_managers_predicate()
        registry = Registry()
        registry.prepare()
        registry.register(tg.request, request)
        registry.register(tg.config, config)
        self.ctrl = AutoCompleteController()

        # Par défaut, l'utilisateur n'est pas identifé.
        tg.request.identity = {'repoze.who.userid': None}

        self.accounts = (
            (u'manager', u'managers'),  # Accès à tout (manager)
            (u'nobody', u'nobody'),     # Accès à rien.
            (u'direct', u'direct'),     # Permissions directe sur l'objet.
            (u'indirect', u'indirect'), # Permissions indirectes sur l'objet.
        )

        # Création des comptes utilisateurs.
        for username, group in self.accounts:
            functions.add_user(username, u'%s@test' % username,
                               u'', u'', group)

        # Création de l'arborescence des objets.
        self.create_deps()

        # Positionnement des permissions.


    def tearDown(self):
        self.ctrl # suspect
        super(AutoCompleterTest, self).tearDown()

    def _change_user(self, user, groups):
        tg.request.identity['repoze.who.userid'] = unicode(user)
        tg.request.environ['repoze.what.credentials']['groups'] = [
            unicode(g) for g in groups
        ]

    def shortDescription(self):
        desc = DbTest.shortDescription(self)
        return "%s (%s)" % (desc, self.__class__.__name__)

    def run(self, result):
        if self.__class__ == AutoCompleterTest:
            return
        return super(AutoCompleterTest, self).run(result)

    def test_no_such_item(self):
        """Autocomplétion sur un élément inexistant."""
        # L'élément n'existe pas : on attend une liste de résultats vide.
        expected = {'results': []}
        for username, group in self.accounts:
            self._change_user(username, [group])

            # On test une première fois en effectuant une recherche exacte.
            res = self._query_autocompleter(u'no_such_graph', False)
            self.assertEqual(res, expected,
                u"Element inexistant/recherche exacte pour %s" % username)

            # Puis une seconde fois avec une recherche partielle.
            res = self._query_autocompleter(u'no_such_graph', True)
            self.assertEqual(res, expected,
                u"Element inexistant/recherche partielle pour %s" % username)

    def test_with_or_without_wildcards(self):
        """Autocomplétion sur nom d'élément avec ou sans jokers."""
        for username, group in self.accounts:
            self._change_user(username, [group])
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
                u"Nom exact en tant que %s" % username)
            # Recherche en utilisant le joker '?'.
            res = self._query_autocompleter(u'f?ob?rb?z', False)
            self.assertEqual(res, expected,
                u"Joker '?' en tant que %s" % username)
            # Recherche en utilisant le joker '*'.
            res = self._query_autocompleter(u'foo*baz', False)
            self.assertEqual(res, expected,
                u"Joker '*' en tant que %s" % username)
            # Recherche en utilisant uniquement le joker '*'.
            res = self._query_autocompleter(u'*', False)
            self.assertEqual(res, expected,
                u"Uniquement '*' en tant que %s" % username)

    def test_partial(self):
        """Autocomplétion sur un nom d'élément en recherche partielle."""
        for username, group in self.accounts:
            self._change_user(username, [group])
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
                u"Recherche partielle avec prefixe en tant que %s" % username)
            expected = {'results': []}
            res = self._query_autocompleter(u'bar', True)
            self.assertEqual(res, expected,
                u"Recherche partielle avec infixe en tant que %s" % username)
            res = self._query_autocompleter(u'barbaz', True)
            self.assertEqual(res, expected,
                u"Recherche partielle avec suffixe en tant que %s" % username)


data_dir = os.path.dirname(os.path.abspath(__file__))
session_dir = os.path.join(data_dir, 'session')

class ApiTest(DbTest):
    def setUp(self):
        super(ApiTest, self).setUp()
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        #environ = {
        #    'repoze.what.credentials': {
        #        'groups': ['managers'],
        #    }
        #}
        #request = Request(environ)
        #registry = Registry()
        #registry.prepare()
        #registry.register(tg.request, request)
        #registry.register(tg.url, request)
        #self.ctrl = AutoCompleteController()

        #tg.request.identity = {
        #    'repoze.who.userid': 'manager',
        #}

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
        #####
        tmpl_options = {}
        tmpl_options['genshi.search_path'] = ['tests']
        self._ctx = ContextObj()
        tmpl_context._push_object(self._ctx)
        self._buffet = pylons.templating.Buffet(
            default_engine='genshi',tmpl_options=tmpl_options
            )
        pylons.buffet._push_object(self._buffet)

    def tearDown(self):
        super(ApiTest, self).tearDown()
        shutil.rmtree(session_dir, ignore_errors=True)

    def shortDescription(self):
        desc = DbTest.shortDescription(self)
        return "%s (%s)" % (desc, self.__class__.__name__)

    def run(self, result):
        if self.__class__ == ApiTest:
            return
        return super(ApiTest, self).run(result)
