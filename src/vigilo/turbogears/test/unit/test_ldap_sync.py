# -*- coding: utf-8 -*-
# Copyright (C) 2006-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

""" Suite de tests du module d'authentification Kerberos"""

from __future__ import print_function
import unittest

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.turbogears.repoze.plugins.mdldapsync import VigiloLdapSync
from vigilo.models.session import DBSession, metadata
from vigilo.models import tables

class FakeLdapConnection(object):
    """
    Classe simulant les objets retournés par
    la méthode initialize de la classe ldap
    """
    def __init__(self, *args, **kwargs):
        self.set_results([])

    def unbind(self):
        """ Simule la méthode unbind mais ne fait rien """
        pass

    def bind_s(self, *args, **kwargs):
        """ Simule la méthode sasl_interactive_bind_s mais ne fait rien """
        pass

    def whoami_s(self):
        """Renvoie le CN de l'utilisateur connecté."""
        return "john.doe"

    def set_results(self, results):
        self._results_index = 0
        self._results = results

    def search_s(self, *args, **kwargs):
        """Remplace la méthode search_s usuelle."""
        if self._results_index >= len(self._results):
            raise IndexError("No more results")
        res = self._results[self._results_index]
        self._results_index += 1
        return res

    def set_option(self, *args, **kwargs):
        """Simule la méthode set_option mais ne fait rien."""
        pass


class FakeLdap(object):
    """ Classe simulant le comportement de la classe ldap """
    def __init__(self, *args, **kwargs):
        self._connection = FakeLdapConnection()

    def initialize(self, *args, **kwargs):
        """ Simule la méthode initialize """
        return self._connection

    def set_results(self, results):
        return self._connection.set_results(results)


class FakeSasl(object):
    """ Classe simulant le comportement de la classe ldap.sasl """

    def gssapi(self):
        """ Simule la méthode gssapi mais ne fait rien """
        return None


class VigiloLdapSyncTest(VigiloLdapSync):
    """
    Classe héritant de la classe VigiloLdapSync et
    destinée à simuler son comportement dans les tests unitaires
    tout en ne contactant pas réellement un annuaire LDAP.
    """

    def __init__(self, *args, **kwargs):
        # Les attributs 'ldap' et 'sasl' de la classe d'origine sont
        # respectivement remplacés par des instances des classes FakeLdap
        # et FakeSasl définies précédemment. Le but est de simuler leur
        # comportement sans avoir à contacter réellement un annuaire LDAP.
        self.ldap = FakeLdap()
        self.sasl = FakeSasl()
        super(VigiloLdapSyncTest, self).__init__(*args, **kwargs)


class TestKerberosAuthentication(unittest.TestCase):
    """ Teste la classe VigiloLdapSync """

    usergroups = [
        u'vigiboard-modification',
        u'vigimap-edition',
        u'vigigraph-consultation',
        u'vigireport-administration',
        u'é'
    ]

    def setUp(self):
        """ Préparation des tests """

        # Préparation de la base de données
        print("Setting up the database...")

        # On crée les tables, puis les vues.
        mapped_tables = metadata.tables.copy()
        views = {}
        for tablename in mapped_tables:
            info = mapped_tables[tablename].info or {}
            if info.get('vigilo_view'):
                views[tablename] = mapped_tables[tablename]
        for view in views:
            del mapped_tables[view]

        metadata.create_all(tables=mapped_tables.itervalues())
        metadata.create_all(tables=views.values())

        # Instanciation de la classe VigiloLdapSyncTest
        # remplaçant la classe VigiloLdapSync pour les tests.
        print("Instanciating Kerberos authentication module...")
        self.plugin = VigiloLdapSyncTest(
            ldap_url='ldap://ldap.example.com',
            user_base='ou=Users,dc=example,dc=com',
            group_base='ou=Groups,dc=example,dc=com',
            binddn='binddn',
            attr_memberof='memberOf',
        )

        # Cas de base : utilisation de memberOf sur les utilisateurs.
        results = [
            # Fiche de l'utilisateur.
            [
                (
                    b'johndoe,dmdName=users,dc=ldap,dc=example,dc=com', {
                        b'memberOf': [
                            b'cn=VIGIBOARD-Modification,ou=Groups,dc=example,dc=com',
                            b'cn=VIGIMAP-Edition,ou=Groups,dc=example,dc=com',
                            b'cn=VIGIGRAPH-Consultation,ou=Groups,dc=example,dc=com',
                            b'cn=VIGIREPORT-Administration,ou=Groups,dc=example,dc=com',
                            b'cn=\xC3\xA9,ou=Groups,dc=example,dc=com'
                        ],
                        b'cn': [b'John Doe'],
                        b'mail': [b'john.doe@example.com']
                    }
                )
            ],
            # Récupération du CN de chacun des groupes.
            [
                (b'cn=VIGIBOARD-Modification,ou=Groups,dc=example,dc=com', {
                    b'cn': [b'VIGIBOARD-Modification'],
                }),
            ],
            [
                (b'cn=VIGIMAP-Edition,ou=Groups,dc=example,dc=com', {
                    b'cn': [b'VIGIMAP-Edition'],
                }),
            ],
            [
                (b'cn=VIGIGRAPH-Consultation,ou=Groups,dc=example,dc=com', {
                    b'cn': [b'VIGIGRAPH-Consultation'],
                })
            ],
            [
                (b'cn=VIGIREPORT-Administration,ou=Groups,dc=example,dc=com', {
                    b'cn': [b'VIGIREPORT-Administration'],
                }),
            ],
            [
                (b'cn=\xC3\xA9,ou=Groups,dc=example,dc=com', {
                    b'cn': [b'\xC3\xA9'],
                }),
            ]
        ]
        self.plugin.ldap.set_results(results)

        self.environ = {
            'repoze.who.logger': LOGGER,
            'KRB5CCNAME': 'johndoe',
        }


    def tearDown(self):
        """ Nettoyage entre les tests """

        print("Dropping the database...")
        DBSession.expunge_all()
        metadata.drop_all()

        self.plugin = None

    def test_user_ldap_info_retrieval(self):
        """
        Récupération des informations de l'utilisateur dans l'annuaire LDAP.
        """
        try:
            (user_fullname, user_email, user_groups) = \
                self.plugin.retrieve_user_ldap_info(
                    self.environ, u'johndoe')
        except Exception, e:
            self.fail("Exception raised while calling "
                    "'retrieve_user_ldap_info': %s." % (e.message, ))

        # On s'assure que les informations récupérées dans
        # l'annuaire LDAP sont conformes à celles attendues.
        self.assertEqual(user_fullname, u"John Doe")
        self.assertEqual(user_email, u'john.doe@example.com')
        self.assertEqual(user_groups, self.usergroups)

        # Cas 2 : il faut utiliser l'attribut "member" des groupes.
        self.plugin.attr_memberof = None
        results = [
            # Résultats pour la recherche parmi les utilisateurs.
            [(
                b'johndoe,dmdName=users,dc=ldap,dc=example,dc=com', {
                    b'cn': [b'John Doe'],
                    b'mail': [b'john.doe@example.com']
                }
            )],
            # Résultats pour la recherche parmi les groupes
            [
                (b'cn=VIGIBOARD-Modification,ou=Groups,dc=example,dc=com', {
                    b'cn': [b'VIGIBOARD-Modification'],
                 }),
                (b'cn=VIGIMAP-Edition,ou=Groups,dc=example,dc=com', {
                    b'cn': [b'VIGIMAP-Edition'],
                }),
                (b'cn=VIGIGRAPH-Consultation,ou=Groups,dc=example,dc=com', {
                    b'cn': [b'VIGIGRAPH-Consultation'],
                }),
                (b'cn=VIGIREPORT-Administration,ou=Groups,dc=example,dc=com', {
                    b'cn': [b'VIGIREPORT-Administration'],
                }),
                (b'cn=\xC3\xA9,ou=Groups,dc=example,dc=com', {
                    b'cn': [b'\xC3\xA9'],
                }),
            ],
        ]
        self.plugin.ldap.set_results(results)

        # Les résultats doivent être identiques à ceux précédemment obtenus.
        try:
            (user_fullname, user_email, user_groups) = \
                self.plugin.retrieve_user_ldap_info(
                    self.environ, u'johndoe')
        except Exception, e:
            self.fail("Exception raised while calling "
                    "'retrieve_user_ldap_info': %s." % (e.message, ))

        self.assertEqual(user_fullname, u"John Doe")
        self.assertEqual(user_email, u'john.doe@example.com')
        self.assertEqual(user_groups, self.usergroups)


    def test_creation(self):
        """
        Création d'un utilisateur et de ses groupes à sa première connexion
        """
        self.plugin.add_metadata({
            'repoze.who.logger': None,
        }, {
            'tokens': ('external', ),
            'repoze.who.userid': u'johndoeé',
        })

        # On vérifie que l'utilisateur a bien été créé
        # et que les données enregistrées sont correctes.
        user = tables.User.by_user_name(u'johndoeé')
        self.assertNotEqual(user, None, 'User not created')

        # On s'assure que les groupes indiqués on bien été créés
        # et que l'utilisateur y appartient bien.
        for ug in self.usergroups:
            usergroup = tables.UserGroup.by_group_name(unicode(ug))
            self.assertNotEqual(usergroup, None,
                u'Missing usergroup (%s)' % ug)

        # On s'assure qu'il n'y a pas de groupes supplémentaires
        # par rapport à ceux demandés.
        for ug in user.usergroups:
            self.assertFalse(ug.group_name not in self.usergroups,
                u'Unexpected usergroup (%s)' % ug.group_name)

    def test_update(self):
        """
        Mise à jour des groupes d'un utilisateur
        """
        identity = {
            'login': u'johndoeé',
            'tokens': ('external', ),
            'repoze.who.userid': u'johndoeé',
        }

        # Création de l'utilisateur ciblé.
        user = tables.User(
            user_name=identity['login'],
            fullname=u'Some Name Here',
            email=u'this.is@a.te.st')
        DBSession.add(user)

        # Création d'un groupe et affectation de l'utilisateur à ce groupe.
        usergroup = tables.UserGroup(group_name=u'SomeOtherGroup')
        DBSession.add(usergroup)
        user.usergroups.append(usergroup)
        DBSession.flush()

        # On appelle le plugin pour synchroniser les informations.
        self.plugin.add_metadata({}, identity)

        # On vérifie que l'utilisateur a bien été créé
        # et que les données enregistrées sont correctes.
        user = tables.User.by_user_name(identity['login'])
        self.assertNotEqual(user, None, 'User not created')

        # On s'assure que les groupes indiqués ont bien été créés
        # et que l'utilisateur y appartient bien.
        for ug in self.usergroups:
            usergroup = tables.UserGroup.by_group_name(unicode(ug))
            self.assertNotEqual(usergroup, None,
                u'Missing usergroup (%s)' % ug)

        # On s'assure qu'il n'y a pas de groupes supplémentaires
        # par rapport à ceux demandés.
        for ug in user.usergroups:
            self.assertFalse(ug.group_name not in self.usergroups,
                u'Unexpected usergroup (%s)' % ug.group_name)

    def test_empty_groups(self):
        """
        Un utilisateur sans groupe doit être correctement géré (#888).
        """
        self.plugin.ldap.set_results([(
            b'johndoe,dmdName=users,dc=ldap,dc=example,dc=com', {
                b'cn': [b'John Doe'],
                b'mail': [b'john.doe@example.com']
            }
        )])

        # Fait appel au plugin pour créer l'utilisateur.
        self.plugin.add_metadata({
            'repoze.who.logger': None,
        }, {
            'tokens': ('external', ),
            'repoze.who.userid': u'johndoeé',
        })

        # On vérifie que l'utilisateur a bien été créé
        # et que les données enregistrées sont correctes.
        user = tables.User.by_user_name(u'johndoeé')
        self.assertNotEqual(user, None, 'User not created')

        # On s'assure qu'aucun groupe n'a été créé/associé
        # pour cet utilisateur.
        for ug in user.usergroups:
            print(ug.group_name)

        self.assertEqual(0, len(user.usergroups))
