# -*- coding: utf-8 -*-
# Copyright (C) 2011-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
"""
import sys, logging
from paste.deploy.converters import asbool
from repoze.who.config import WhoConfig, _LEVELS
from repoze.who.middleware import PluggableAuthenticationMiddleware
from tg.configuration.auth.setup import _AuthenticationForgerPlugin


class VigiloAuthMiddleware(PluggableAuthenticationMiddleware):
    """
    Un middleware d'authentification basé sur C{repoze.who}
    mais qui n'effectue pas un pass-through lorsque la variable
    d'environnement contenant l'identifiant de l'utilisateur
    (généralement C{REMOTE_USER}) est pré-remplie.

    Ceci permet de toujours appeler les modules qui agissent lors
    des phases post-authentification (challenger, mdproviders).
    """

    def __init__(self,
                 app,
                 identifiers,
                 authenticators,
                 challengers,
                 mdproviders,
                 request_classifier = None,
                 challenge_decider = None,
                 log_stream = None,
                 log_level = logging.INFO,
                 remote_user_key = 'REMOTE_USER',
                 classifier = None):
        super(VigiloAuthMiddleware, self).__init__(
            app, identifiers, authenticators, challengers, mdproviders,
            request_classifier, challenge_decider,
            log_stream, log_level, remote_user_key, classifier)

        # Evite que repoze ne court-circuite l'exécution des plugins,
        # et en particulier celle des fournisseurs de méta-données,
        # lorsqu'une authentification externe a eu lieu.
        self.remote_user_key = None

        # On doit néanmoins mémoriser la valeur de remote_user_key
        # pour la passer aux plugins (via l'environnement).
        self.actual_remote_user_key = remote_user_key

    def __call__(self, environ, start_response):
        """
        Cette méthode est inspirée de
        C{repoze.who.middleware.PluggableAuthenticationMiddleware:__call__}.

        Ici, les plugins sont systématiquement appelés (en particulier
        les plugins de type mdprovider).

        La clé "repoze.who.remote_user_key" contiendra le nom de la clé
        de l'environnement contenant le nom du l'utilisateur pré-authentifié
        (en cas d'authentification externe).
        """
        environ['repoze.who.remote_user_key'] = self.actual_remote_user_key
        return super(VigiloAuthMiddleware, self).__call__(environ, start_response)


class VigiloAuthForgerPlugin(_AuthenticationForgerPlugin):
    def challenge(self, environ, status, app_headers, forget_headers):
        """
        Retourne systématiquement une page d'erreur 401.

        Retire également un éventuel en-tête "Content-Lenght" erroné.
        """
        app_headers = filter(lambda h: h[0].lower() != 'content-length', app_headers)
        forget_headers = filter(lambda h: h[0].lower() != 'content-length', forget_headers)
        return super(VigiloAuthForgerPlugin, self).challenge(
                    environ, status, app_headers, forget_headers)

    def authenticate(self, environ, identity):
        res = super(VigiloAuthForgerPlugin, self).authenticate(
                    environ, identity)

        # On force l'encodage (la BDD de Vigilo utilise des champs Unicode).
        if res is not None and not isinstance(res, unicode):
            res = res.decode('utf-8')
        return res


class VigiloAuthForgerMiddleware(VigiloAuthMiddleware):
    """
    Un middleware inspiré de
    C{repoze.who.plugins.testutil:AuthenticationForgerMiddleware}
    et qui simule le fonctionnement du middleware d'authentification.

    Ce middleware est destiné aux tests unitaires et permet également
    de simuler l'utilisation d'un mécanisme d'authentification externe
    avec Vigilo.
    """
    plugin_factory = VigiloAuthForgerPlugin

    def __init__(self, app, identifiers, authenticators, challengers,
                 mdproviders, request_classifier=None, challenge_decider=None,
                 log_stream=None, log_level=logging.INFO,
                 remote_user_key='REMOTE_USER', classifier=None):
        """
        Setup authentication in an easy to forge way.

        All the arguments received will be passed as is to
        :class:`VigiloAuthForgerMiddleware`,
        with one instance of :class:`VigiloAuthForgerPlugin` in:

        * ``identifiers``. This instance will be inserted in the first position
          of the list.
        * ``authenticators``. Any authenticator passed will be ignored; such
          an instance will be the only authenticator defined.
        * ``challengers``. Any challenger passed will be ignored; such
          an instance will be the only challenger defined.

        The metadata providers won't be modified.

        """
        self.actual_remote_user_key = remote_user_key
        forger = self.plugin_factory(fake_user_key=remote_user_key)
        forger = ('auth_forger', forger)
        identifiers.insert(0, forger)
        authenticators = [forger]
        challengers = [forger]
        init = super(VigiloAuthForgerMiddleware, self).__init__
        # On laisse remote_user_key prendre sa valeur par défaut (REMOTE_USER)
        # pour éviter une interférence entre repoze.who.testutil et nos
        # propres modifications (cf. VigiloAuthMiddleware).
        #remote_user_key = 'repoze.who.testutil.userid'
        init(app, identifiers, authenticators, challengers, mdproviders,
             request_classifier, challenge_decider, log_stream, log_level,
             remote_user_key, classifier)

    def __call__(self, environ, start_response):
        """
        Appelle le middleware d'authentification de test.
        """
        return super(VigiloAuthForgerMiddleware, self).__call__(
                    environ, start_response)


def _mk_mw_cfg(app, global_conf, config_file,
                log_stream=None, log_level=None):
    """
    Inspiré par C{repoze.who.config:make_middleware_with_config}.
    """
    parser = WhoConfig(global_conf['here'])
    parser.parse(open(config_file))

    if log_level is None:
        log_level = logging.INFO
    elif isinstance(log_level, basestring):
        log_level = _LEVELS[log_level.lower()]

    return VigiloAuthMiddleware(
                app,
                parser.identifiers,
                parser.authenticators,
                parser.challengers,
                parser.mdproviders,
                parser.request_classifier,
                parser.challenge_decider,
                log_stream,
                log_level,
                parser.remote_user_key,
           )


def make_middleware_with_config(app, global_conf, config_file, log_stream=None,
                                log_level=None, skip_authentication=False):
    """
    Proxy :func:`repoze.who.config.make_middleware_with_config` to skip
    authentication when required.

    If  ``skip_authentication`` evaluates to ``True``, then the returned
    middleware will be an instance of :class:`VigiloAuthForgerMiddleware`.

    Inspiré par C{repoze.who.plugins.testutil:make_middleware_with_config}.
    """
    if not asbool(skip_authentication):
        # We must not replace the middleware
        return _mk_mw_cfg(app, global_conf, config_file, log_stream, log_level)

    # We must replace the middleware:
    parser = WhoConfig(global_conf['here'])
    parser.parse(open(config_file))
    return VigiloAuthForgerMiddleware(
        app,
        parser.identifiers,
        parser.authenticators,
        parser.challengers,
        parser.mdproviders,
        parser.request_classifier,
        parser.challenge_decider,
        remote_user_key=parser.remote_user_key,
        )
