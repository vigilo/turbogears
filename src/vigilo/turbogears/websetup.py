# -*- coding: utf-8 -*-
"""Peuple la base de données."""

import logging

import transaction
from tg import config

__all__ = ['populate_db']

log = logging.getLogger(__name__)

def populate_db():
    """Placez les commandes pour peupler la base de données ici."""
    from vigilo.models.session import DBSession
    from vigilo.models.vigilo_bdd_config import metadata

    # Chargement du modèle.
    from vigilo import models

    # Création des tables
    print "Creating tables"
    # XXX Pour une raison inconnue, metadata.bind est défini
    # à la place de DBSession.bind durant les tests unitaires.
    if metadata.bind is None:
        metadata.bind = DBSession.bind
    metadata.create_all()

    # Création d'un jeu de données par défaut.
    manager = models.User()
    manager.user_name = u'manager'
    manager.email = u'manager@somedomain.com'
    manager.fullname = u'Manager'
    manager.password = u'managepass'
    DBSession.add(manager)

    group = models.UserGroup()
    group.group_name = u'managers'
    group.users.append(manager)
    DBSession.add(group)

    permission = models.Permission()
    permission.permission_name = u'manage'
    permission.usergroups.append(group)
    DBSession.add(permission)

    editor = models.User()
    editor.user_name = u'editor'
    editor.email = u'editor@somedomain.com'
    editor.fullname = u'Editor'
    editor.password = u'editpass'
    DBSession.add(editor)

    group = models.UserGroup()
    group.group_name = u'editors'
    group.users.append(editor)
    DBSession.add(group)

    permission = models.Permission()
    permission.permission_name = u'edit'
    permission.usergroups.append(group)
    DBSession.add(permission)

    # XXX Ajouter un identifiant de version correspondant au modèle.
#    version = Version()
#    version.name = u'vigicore'
#    version.version = config['vigicore_version']
#    DBSession.add(version)

    DBSession.flush()
    transaction.commit()
    print "Successfully setup"

