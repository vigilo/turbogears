# -*- coding: utf-8 -*-
"""
Ce module contient un contrôleur pour TurboGears qui centralise
la gestion des méthodes relatives à l'authentification.

Les applications feront généralement hériter leur contrôleur
principal de celui-ci.
"""

import logging
from pylons.i18n import ugettext as _
from tg import session, request, expose, flash, redirect, session, config
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

        userid = request.identity['repoze.who.userid']
        LOGGER.info(_('"%(username)s" logged into %(app)s (from %(IP)s)') % {
                'username': userid,
                'IP': request.remote_addr,
                'app': config.app_name,
            })
        flash(_('Welcome back, %s!') % userid)
        redirect(came_from)

    @expose()
    def post_logout(self, came_from='/', **kw):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.
        """
        username = None

        # @TODO: généraliser + traiter l'auth interne correctement.
        if not session.get('vigilo'):
            msg = _('Some user logged out from %(app)s (from %(IP)s)')
        else:
            msg = _('"%(username)s" logged out from %(app)s (from %(IP)s)')
            username = session['vigilo']

        LOGGER.info(msg % {
                'username': username,
                'IP': request.remote_addr,
                'app': config.app_name,
            })
        flash(_('We hope to see you soon!'))
        session.delete()
        redirect(came_from)
