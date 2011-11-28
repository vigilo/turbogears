# -*- coding: utf-8 -*-
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

""" Suite de tests du module d'authentification Kerberos"""

import unittest

from vigilo.common.conf import settings
settings.load_file('settings_tests.ini')

from vigilo.models.configure import configure_db
configure_db(settings['database'], 'sqlalchemy_')

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.turbogears.repoze.plugins.mdldapsync import VigiloLdapSync
from vigilo.models.session import DBSession, metadata
from vigilo.models import tables
from vigilo.models.tables.grouppath import GroupPath
from vigilo.models.tables.usersupitem import UserSupItem

class FakeLdapConnection(object):
    """
    Classe simulant les objets retournés par
    la méthode initialize de la classe ldap
    """
    def __init__(self, *args, **kwargs):
        self._result = [(
            'johndoe,dmdName=users,dc=ldap,dc=example,dc=com', {
                'memberOf': [
                    u'cn=VIGIBOARD-Modification,dmdName=droits,'
                        'dc=ldap,dc=example,dc=com',
                    u'cn=VIGIMAP-Edition,dmdName=droits,'
                        'dc=ldap,dc=example,dc=com',
                    u'cn=VIGIGRAPH-Consultation,dmdName=droits,'
                        'dc=ldap,dc=example,dc=com',
                    u'cn=VIGIREPORT-Administration,dmdName=droits,'
                        'dc=ldap,dc=example,dc=com',
                    # On spécifie un nom contenant un caractère accentué,
                    # encodé en utilisant l'alphabet ISO-8859-1.
                    # Il s'agit ici d'un "é".
                    'cn=\xE9,dmdName=droits,'
                        'dc=ldap,dc=example,dc=com'
                ],
                'cn': [u'John Doe'],
                'mail': [u'john.doe@example.com']
            }
        )]

    def unbind(self):
        """ Simule la méthode unbind mais ne fait rien """
        pass

    def sasl_interactive_bind_s(self, *args, **kwargs):
        """ Simule la méthode sasl_interactive_bind_s mais ne fait rien """
        pass

    def whoami_s(self):
        """Renvoie le CN de l'utilisateur connecté."""
        return "john.doe"

    def set_return_value(self, result):
        self._result = result

    def search_s(self, *args, **kwargs):
        """ Remplace la méthode search_s usuelle."""
        return self._result

class FakeLdap(object):
    """ Classe simulant le comportement de la classe ldap """

    SCOPE_SUBTREE = None

    def __init__(self, *args, **kwargs):
        self._connection = FakeLdapConnection()

    def initialize(self, *args, **kwargs):
        """ Simule la méthode initialize """
        return self._connection

    def set_return_value(self, result):
        return self._connection.set_return_value(result)

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

    def setUp(self):
        """ Préparation des tests """

        # Préparation de la base de données
        print "Setting up the database..."

        # La vue GroupPath dépend de Group et GroupHierarchy.
        # SQLAlchemy ne peut pas détecter correctement la dépendance.
        # On crée le schéma en 2 fois pour contourner ce problème.
        # Idem pour la vue UserSupItem (6 dépendances).
        mapped_tables = metadata.tables.copy()
        del mapped_tables[GroupPath.__tablename__]
        del mapped_tables[UserSupItem.__tablename__]
        metadata.create_all(tables=mapped_tables.itervalues())
        metadata.create_all(
            tables=[GroupPath.__table__, UserSupItem.__table__])

        # Instanciation de la classe VigiloLdapSyncTest
        # remplaçant la classe VigiloLdapSync pour les tests.
        print "Instanciating Kerberos authentication module..."
        self.plugin = VigiloLdapSyncTest(
            '', '',
            ldap_charset='iso-8859-1'
        )

        #
        self.environ = {
            'repoze.who.logger': LOGGER,
            'KRB5CCNAME': 'johndoe',
        }

        import logging
        logging.basicConfig()

    def tearDown(self):
        """ Nettoyage entre les tests """

        print "Dropping the database..."
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
                    self.environ, 'johndoe')
        except Exception, e:
            self.fail("Exception raised while calling "
                    "'retrieve_user_ldap_info': %s." % (e.message, ))

        # On s'assure que les informations récupérées dans
        # l'annuaire LDAP sont conformes à celles attendues.
        self.assertEquals(user_fullname, u"John Doe")
        self.assertEquals(user_email, u'john.doe@example.com')
        self.assertEquals(user_groups, [
            u'vigiboard-modification',
            u'vigimap-edition',
            u'vigigraph-consultation',
            u'vigireport-administration',
            u'é'
        ])

    def test_creation(self):
        """
        Création d'un utilisateur et de ses groupes à sa première connexion
        """

        usergroups = [
            u'vigiboard-modification',
            u'vigimap-edition',
            u'vigigraph-consultation',
            u'vigireport-administration',
            u'é',
        ]
        self.plugin.add_metadata({
            'repoze.who.logger': None,
            # La séquence "\xC3\xA9" correspond à un "é"
            # encodé en UTF-8. On vérifie ici que le module
            # est capable de décoder correctement ce genre
            # de "principals" à l'aide du paramètre "http_charset".
            'REMOTE_USER': 'johndoe\xC3\xA9@example.com',
        }, {})

        # On vérifie que l'utilisateur a bien été créé
        # et que les données enregistrées sont correctes.
        user = tables.User.by_user_name(u'johndoeé')
        self.failIfEqual(user, None, 'User not created')

        # On s'assure que les groupes indiqués on bien été créés
        # et que l'utilisateur y appartient bien.
        for ug in usergroups:
            usergroup = tables.UserGroup.by_group_name(unicode(ug))
            self.failIfEqual(usergroup, None,
                u'Missing usergroup (%s)' % ug)

        # On s'assure qu'il n'y a pas de groupes supplémentaires
        # par rapport à ceux demandés.
        for ug in user.usergroups:
            self.failIf(ug.group_name not in usergroups,
                u'Unexpected usergroup (%s)' % ug.group_name)

    def test_update(self):
        """
        Mise à jour des groupes d'un utilisateur
        """

        usergroups = [
            u'vigiboard-modification',
            u'vigimap-edition',
            u'vigigraph-consultation',
            u'vigireport-administration',
            u'é'
        ]
        identity = {
            'login': u'johndoeé',
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

        # On fait appel au plugin pour mettre à jour les informations.
        environ = self.environ.copy()
        environ['REMOTE_USER'] = 'johndoe\xC3\xA9@example.com'
        self.plugin.add_metadata(environ, identity)

        # On vérifie que l'utilisateur a bien été créé
        # et que les données enregistrées sont correctes.
        user = tables.User.by_user_name(identity['login'])
        self.failIfEqual(user, None, 'User not created')

        # On s'assure que les groupes indiqués ont bien été créés
        # et que l'utilisateur y appartient bien.
        for ug in usergroups:
            usergroup = tables.UserGroup.by_group_name(unicode(ug))
            self.failIfEqual(usergroup, None,
                u'Missing usergroup (%s)' % ug)

        # On s'assure qu'il n'y a pas de groupes supplémentaires
        # par rapport à ceux demandés.
        for ug in user.usergroups:
            self.failIf(ug.group_name not in usergroups,
                u'Unexpected usergroup (%s)' % ug.group_name)

    def test_empty_groups(self):
        """
        Un utilisateur sans groupe doit être correctement géré (#888).
        """
        self.plugin.ldap.set_return_value([(
            'johndoe,dmdName=users,dc=ldap,dc=example,dc=com', {
                'cn': [u'John Doe'],
                'mail': [u'john.doe@example.com']
            }
        )])

        # Fait appel au plugin pour créer l'utilisateur.
        self.plugin.add_metadata(
            {
                'repoze.who.logger': None,
                # La séquence "\xC3\xA9" correspond à un "é"
                # encodé en UTF-8. On vérifie ici que le module
                # est capable de décoder correctement ce genre
                # de "principals" à l'aide du paramètre "http_charset".
                'REMOTE_USER': 'johndoe\xC3\xA9@example.com',
            },
            {},
        )

        # On vérifie que l'utilisateur a bien été créé
        # et que les données enregistrées sont correctes.
        user = tables.User.by_user_name(u'johndoeé')
        self.failIfEqual(user, None, 'User not created')

        # On s'assure qu'aucun groupe n'a été créé/associé
        # pour cet utilisateur.
        for ug in user.usergroups:
            print ug.group_name

        self.assertEqual(0, len(user.usergroups))