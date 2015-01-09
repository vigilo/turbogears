# -*- coding: utf-8 -*-
# Copyright (C) 2006-2015 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Configuration de modules fournissant des métadonnées
pour le framework repoze.who.

Ce module ajoute automatiquement les instances des groupes
d'utilisateurs auxquels l'utilisateur identifié appartient
dans l'environnement de la requête.
"""

from repoze.what.plugins.sql import configure_sql_adapters
from repoze.what.middleware import AuthorizationMetadata
from vigilo.models import tables, session
from .translation import translations

_source_adapters = configure_sql_adapters(
    tables.User,
    tables.UserGroup,
    tables.Permission,
    session.DBSession,
    translations['group_adapter'],
    translations['permission_adapter'],
)

# Fournisseur de méta-données.
plugin = AuthorizationMetadata(
    {'sqlauth': _source_adapters['group']},
    {'sqlauth': _source_adapters['permission']},
)
