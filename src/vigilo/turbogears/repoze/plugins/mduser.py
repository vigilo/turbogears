# -*- coding: utf-8 -*-
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Configuration de modules fournissant des métadonnées
pour le framework repoze.who.

Ce plugin ajoute automatiquement l'instance correspondant à
l'utilisateur identifié dans l'environnement de la requête.
"""

from repoze.who.plugins.sa import SQLAlchemyUserMDPlugin
from vigilo.models import tables, session

# Fournisseur de méta-données.
class plugin(SQLAlchemyUserMDPlugin):
    def __init__(self):
        super(plugin, self).__init__(tables.User, session.DBSession)

    def add_metadata(self, environ, identity):
        user = self.get_user(identity['repoze.who.userid'])
        groups = set()
        permissions = set()

        if user:
            identity['fullname'] = user.fullname
            for group in user.usergroups:
                groups.add(group.group_name)
                for perm in group.permissions:
                    permissions.add(perm.permission_name)

        identity['groups'] = groups
        identity['permissions'] = permissions

        if 'repoze.what.credentials' not in environ:
            environ['repoze.what.credentials'] = {}
        environ['repoze.what.credentials'].update(identity)
