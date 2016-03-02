# -*- coding: utf-8 -*-
# Copyright (C) 2006-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Configuration de modules fournissant des métadonnées
pour le framework repoze.who.

Ce plugin ajoute automatiquement l'instance correspondant à
l'utilisateur identifié dans l'environnement de la requête.

Ces différents modules sont utilisables via un fichier who.ini.
"""

from repoze.who.plugins.sa import SQLAlchemyUserMDPlugin
from repoze.what.plugins.quickstart import find_plugin_translations
from vigilo.models import tables, session
from .translation import translations

# Fournisseur de méta-données.
plugin = SQLAlchemyUserMDPlugin(tables.User, session.DBSession)
plugin.translations.update(translations['mdprovider'])
