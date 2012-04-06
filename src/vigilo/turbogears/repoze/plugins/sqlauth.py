# -*- coding: utf-8 -*-
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce fichier contient un module permettant d'authentifier
un utilisateur vis-à-vis de la base de données de Vigilo.

Il doit être utilisé dans le cadre du framework repoze.who
via le fichier de configuration who.ini.
"""

from repoze.who.plugins.sa import SQLAlchemyAuthenticatorPlugin
from vigilo.models import tables, session
from .translation import translations

# Authentification.
plugin = SQLAlchemyAuthenticatorPlugin(tables.User, session.DBSession)
plugin.translations.update(translations['authenticator'])
