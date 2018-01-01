# -*- coding: utf-8 -*-
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce fichier contient un module permettant d'authentifier
un utilisateur vis-à-vis de la base de données de Vigilo.

Il doit être utilisé dans le cadre du framework repoze.who
via le fichier de configuration who.ini.
"""

from repoze.who.plugins.sa import SQLAlchemyAuthenticatorPlugin
from vigilo.models import tables, session

class VigiloSAAuthenticatorPlugin(SQLAlchemyAuthenticatorPlugin):
    def authenticate(self, environ, identity):
        res = super(VigiloSAAuthenticatorPlugin, self).authenticate(
                environ, identity)

        if 'login' in identity and res is None:
            logger = environ.get('repoze.who.logger')
            logger and logger.warn(
                'Wrong credentials for user "%(user_login)s" '
                '(from %(user_ip)s)', {
                'user_login': identity['login'],
                'user_ip': environ.get('REMOTE_ADDR') or '0.0.0.0',
            })
        return res

# Authentification.
plugin = VigiloSAAuthenticatorPlugin(tables.User, session.DBSession)
