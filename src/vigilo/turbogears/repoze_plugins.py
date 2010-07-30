# -*- coding: utf-8 -*-
"""
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
    if PATH_INFO(environ).find('/api/') != -1:
        return 'vigilo-api'
    return default_request_classifier(environ)
zope.interface.directlyProvides(vigilo_api_classifier, IRequestClassifier)

from repoze.what.plugins.pylonshq import booleanize_predicates
booleanize_predicates()
