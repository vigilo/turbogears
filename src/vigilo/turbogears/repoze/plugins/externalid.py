# -*- coding: utf-8 -*-
# Copyright (C) 2011-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Un module d'identification pour le framework repoze.who
qui permet de pré-authentifier l'utilisateur à partir
d'une source externe (p.ex. authentification Apache).
"""

from zope.interface import implements
from repoze.who.interfaces import IIdentifier, IAuthenticator


class ExternalIdentification(object):
    """
    Cette classe détecte les pré-authentifications réalisées
    à partir d'une source externe.
    """

    implements(IIdentifier, IAuthenticator)

    def __init__(self, rememberer, strip_realm=True):
        """
        Initialise le plugin de gestion des authentifications externes.

        @param strip_realm: Indique si le royaume doit être supprimé ou conservé
            lorsque l'authentification externe fournit une identité basée
            sur un principal.Kerberos (user@REALM).
            Par défaut, le royaume est supprimé.
        @type strip_realm: bool
        @param rememberer: Nom du plugin chargé de mémoriser l'identité
            de l'utilisateur une fois celui-ci authentifié.
        @type rememberer: str
        """
        if isinstance(strip_realm, bool):
            strip_realm = str(strip_realm)
        strip_realm = unicode(strip_realm, 'utf-8', 'replace').lower()
        if strip_realm in ('true', 'yes', 'on', '1'):
            strip_realm = True
        elif strip_realm in ('false', 'no', 'off', '0'):
            strip_realm = False
        else:
            raise ValueError('A boolean value was expected for "strip_realm"')
        self.strip_realm = strip_realm
        self.rememberer = rememberer

    def _get_rememberer(self, environ):
        rememberer = environ['repoze.who.plugins'].get(self.rememberer)
        return rememberer

    def _get_remote_user(self, environ):
        remote_user_key = environ.get('repoze.who.remote_user_key')
        if not remote_user_key:
            return None

        remote_user = environ.get(remote_user_key)
        if remote_user is None:
            return None

        if self.strip_realm:
            remote_user = remote_user.split('@', 1)[0]
        return remote_user

    # IIdentifier
    def remember(self, environ, identity):
        rememberer = self._get_rememberer(environ)
        if not rememberer:
            return []
        return rememberer.remember(environ, identity)

    # IIdentifier
    def forget(self, environ, identity):
        rememberer = self._get_rememberer(environ)
        if not rememberer:
            return []
        return rememberer.forget(environ, identity)

    # IIdentifier
    def identify(self, environ):
        """
        Inspecte l'environnement de la requête afin de vérifier
        si l'utilisateur a déjà été authentifié précédemment ou non.
        En cas de concordance, l'identité précédente est réutilisée.

        @param environ: Environnement WSGI de la requête HTTP.
        @type environ: C{dict}
        @return: Dictionnaire pré-authentifiant l'utilisateur ou C{None}.
        @rtype: C{dict} or C{None}
        """
        remote_user = self._get_remote_user(environ)
        if remote_user is None:
            return None
        return {'login': remote_user, 'password': ''}

    # IAuthenticator
    def authenticate(self, environ, identity):
        """
        Inspecte l'environnement de la requête afin de vérifier
        si l'utilisateur a déjà été authentifié précédemment ou non.
        En cas de concordance, l'identité précédente est fait foi.

        @param environ: Environnement WSGI de la requête HTTP.
        @type environ: C{dict}
        @return: Identifiant de l'utilisateur (pré-)authentifié.
        @rtype: C{str}
        """
        try:
            login = identity['login']
        except KeyError:
            return None

        remote_user = self._get_remote_user(environ)
        if not remote_user or remote_user != login:
            return None

        # L'utilisateur a été pré-authentifié via une source externe.
        # On garde une trace de cette information.
        environ['vigilo.external_auth'] = True
        return login
