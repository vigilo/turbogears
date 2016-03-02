# -*- coding: utf-8 -*-
# Copyright (C) 2011-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Un module d'identification pour le framework repoze.who
qui permet de pré-authentifier l'utilisateur à partir
d'une session Beaker.

Ce module est généralement utilisé conjointement avec le module
de synchronisation LDAP (qui se charge d'alimenter la session).
"""

class ExternalIdentification(object):
    """
    Cette classe agit comme un identificateur pour repoze.who
    et pré-authentifie l'utilisateur à partir d'une session Beaker.
    """

    def __init__(self, cache_name):
        """
        Initialisation du module d'identification.

        @param cache_name: Nom de la clé à recherche dans la session
            et qui contient l'identifiant sous lequel l'utilisateur
            doit être pré-authentifié.
        @type cache_name: C{basestring}
        """
        self.cache_name = cache_name

    def identify(self, environ):
        """
        Inspecte la session Beaker en cours afin de vérifier
        si l'utilisateur s'est déjà authentifié précédemment
        ou non.

        Dans le cas positif, l'identité précédente est réutilisée
        pour pré-authentifier l'utilisateur.

        @param environ: Environnement WSGI de la requête HTTP.
        @type environ: C{dict}
        @return: Dictionnaire pré-authentifiant l'utilisateur ou None.
        @rtype: C{dict} or C{None}
        """
        if 'beaker.session' not in environ:
            return None
        if self.cache_name not in environ['beaker.session']:
            return None
        remote_user = environ['beaker.session'][self.cache_name]
        return {'login': remote_user, 'repoze.who.userid': remote_user}

    def remember(self, environ, identity):
        """
        Cette méthode n'est pas pertinente dans le cas de ce module.

        @param environ: Environnement WSGI de la requête HTTP.
        @type environ: C{dict}
        @param identity: Identité de l'utilisateur à mémoriser.
        @type identity: C{dict}
        """
        pass

    def forget(self, environ, identity):
        """
        Cette méthode n'est pas pertinente dans le cas de ce module.

        @param environ: Environnement WSGI de la requête HTTP.
        @type environ: C{dict}
        @param identity: Identité de l'utilisateur à mémoriser.
        @type identity: C{dict}
        """
        pass
