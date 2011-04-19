# -*- coding: utf-8 -*-
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Configuration de modules pour le framework repoze.who.
Ces différents modules seront utilisables
dans le fichier who.ini.
"""

import zope.interface
from repoze.who.interfaces import IRequestClassifier

from repoze.who.plugins.sa import (
    SQLAlchemyAuthenticatorPlugin,
    SQLAlchemyUserMDPlugin,
)
from repoze.what.plugins.sql import configure_sql_adapters
from repoze.what.middleware import AuthorizationMetadata
from repoze.what.plugins.quickstart import find_plugin_translations
from repoze.who.classifiers import default_request_classifier

from vigilo.models import tables, session

_plugin_translations = find_plugin_translations({
    'groups': 'usergroups',
})

# Authentification.
# Ce plugin permet d'authentifier les utilisateurs vis-à-vis
# de la base de données.
auth_plugin = SQLAlchemyAuthenticatorPlugin(tables.User, session.DBSession)
auth_plugin.translations.update(_plugin_translations['authenticator'])

# Fournisseur de méta-données.
# Ce plugin ajoute automatiquement l'instance correspondant à
# l'utilisateur identifié dans l'environnement de la requête.
md_plugin = SQLAlchemyUserMDPlugin(tables.User, session.DBSession)
md_plugin.translations.update(_plugin_translations['mdprovider'])

_source_adapters = configure_sql_adapters(
    tables.User,
    tables.UserGroup,
    tables.Permission,
    session.DBSession,
    _plugin_translations['group_adapter'],
    _plugin_translations['permission_adapter'],
)

# Fournisseur de méta-données.
# Ce plugin ajoute automatiquement les instances des groupes
# d'utilisateurs auxquels l'utilisateur identifié appartient
# dans l'environnement de la requête.
md_group_plugin = AuthorizationMetadata(
    {'sqlauth': _source_adapters['group']},
    {'sqlauth': _source_adapters['permission']},
)

def vigilo_api_classifier(environ):
    from paste.httpheaders import PATH_INFO
    # On classe à part les données statiques, ce qui évite
    # de leur appliquer un test d'authentification.
    # Il faut faire une exception pour les proxies
    # car là on veut procéder à une authentification.
    ext = PATH_INFO(environ).rpartition('.')
    if '/vigirrd/' not in PATH_INFO(environ) and \
        '/nagios/' not in PATH_INFO(environ) and \
        ext[2] in ('png', 'jpg', 'gif', 'css', 'js'):
        return 'static'
    if '/api/' in PATH_INFO(environ):
        return 'vigilo-api'
    return default_request_classifier(environ)
zope.interface.directlyProvides(vigilo_api_classifier, IRequestClassifier)

from repoze.what.plugins.pylonshq import booleanize_predicates
booleanize_predicates()
