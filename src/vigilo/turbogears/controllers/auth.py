# -*- coding: utf-8 -*-
# Copyright (C) 2011-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce module contient un contrôleur pour TurboGears qui centralise
la gestion des méthodes relatives à l'authentification.

Les applications feront généralement hériter leur contrôleur
principal de celui-ci.
"""

import logging
from pylons.i18n import ugettext as _
from tg import request, expose, flash, redirect, config
from vigilo.turbogears.controllers import BaseController

LOGGER = logging.getLogger(__name__)

class AuthController(BaseController):
    @expose('login.html')
    def login(self, came_from='/', **kw):
        """Start the user login."""
        # Si l'utilisateur a déjà été authentifié automatiquement par un
        # mécanisme externe, on le redirige vers la page d'origine.
        # On prend soin de retirer le message demandant une authentification
        # qui se trouve dans la pile de messages de la méthode flash().
        if request.identity and request.identity.get('repoze.who.userid'):
            flash.pop_payload()
            redirect(came_from)

        login_counter = request.environ.get('repoze.who.logins', 0)
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from)

    @expose()
    def post_login(self, came_from='/', **kw):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.
        """
        if not request.identity:
            login_counter = request.environ.get('repoze.who.logins', 0) + 1
            redirect('/login',  came_from=came_from, __logins=login_counter)

        # On enregistre les connexions dans le logger des authentifications.
        # Voir aussi vigilo.turbogears.repoze.plugins.friendlyform
        # et vigilo.turbogears.repoze.plugins.sqlauth qui enregistrent
        # des logs pour des cas similaires (déconnexion et échec de
        # l'authentification).
        logger = logging.getLogger('auth')
        userid = request.identity['repoze.who.userid']
        logger.info(
            'User "%(user_login)s" logged in (from %(user_ip)s)', {
                'user_login': userid,
                # vigilo.common.logging ne pourra pas déterminer l'identité de
                # l'utilisateur car l'authentification n'est pas complètement
                # finie. On fournit "user_fullname" explicitement pour écraser
                # la valeur "???" auto-déterminée.
                'user_fullname': request.identity['user'].fullname,
                'user_ip': request.remote_addr,
            })
        flash(_('Welcome back, %s!') % userid)
        redirect(came_from)

    @expose()
    def post_logout(self, came_from='/', **kw):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.
        """
        flash(_('We hope to see you soon!'))
        redirect(came_from)
