# -*- coding: utf-8 -*-
"""
"""
import sys, logging
from paste.deploy.converters import asbool
from repoze.who.plugins.testutil import AuthenticationForgerMiddleware
from repoze.who.config import WhoConfig, _LEVELS
from repoze.who.middleware import PluggableAuthenticationMiddleware, Identity, \
                                    _STARTED, _ENDED, StartResponseWrapper, \
                                    wrap_generator

class VigiloAuthMiddleware(PluggableAuthenticationMiddleware):
    """
    Un middleware d'authentification basé sur C{repoze.who}
    mais qui n'effectue pas un pass-through lorsque la variable
    d'environnement contenant l'identifiant de l'utilisateur
    (généralement C{REMOTE_USER}) est pré-remplie.

    Ceci permet de toujours appeler les modules qui agissent lors
    des phases post-authentification (challenger, mdproviders).
    """

    def __call__(self, environ, start_response):
        """
        Cette méthode est inspirée de
        C{repoze.who.middleware.PluggableAuthenticationMiddleware:__call__}.

        La différence réside dans le fait que la méthode originale
        désactive complètement le middleware d'authentification
        lorsqu'un identifiant d'utilisateur est passé dans l'environnement
        (par exemple, via la variable C{REMOTE_USER}).

        Au contraire, cette version s'assure que les modules qui
        interviennent après les processus d'identification et
        d'authentification de l'utilisateur sont quand même appelés.

        Ceci permet par exemple de récupérer des informations importantes
        concernant l'utilisateur (depuis la base de données par exemple)
        via les modules fournisseurs de méta-données (mdproviders).
        """
        path_info = environ.get('PATH_INFO', None)

        environ['repoze.who.plugins'] = self.name_registry
        environ['repoze.who.logger'] = self.logger
        environ['repoze.who.application'] = self.app
        environ['vigilo.external_auth'] = False

        logger = self.logger
        logger and logger.info(_STARTED % path_info)
        classification = self.classifier(environ)
        logger and logger.info('request classification: %s' % classification)
        identity = None
        identifier = None

        userid = environ.get(self.remote_user_key)
        if userid:
            logger and logger.info('using external identity: %s' % userid)
            # Pas besoin d'effectuer les phases d'identification
            # et d'authentification si elles ont déjà été faites en amont.
            identity = {
                'login': userid,
                'password': None,
                'repoze.who.userid': userid,
            }
            # Marque l'utilisateur comme identifié par un mécanisme externe.
            environ['vigilo.external_auth'] = True

        else:
            ids = self.identify(environ, classification)

            # ids will be list of tuples: [ (IIdentifier, identity) ]
            if ids:
                auth_ids = self.authenticate(environ, classification, ids)

                # auth_ids will be a list of five-tuples in the form
                #  ( (auth_rank, id_rank), authenticator, identifier, identity,
                #    userid )
                #
                # When sorted, its first element will represent the "best"
                # identity for this request.

                if auth_ids:
                    auth_ids.sort()
                    best = auth_ids[0]
                    rank, authenticator, identifier, identity, userid = best

            else:
                logger and logger.info('no identities found, not authenticating')

        # Même si un mécanisme externe d'authentification a été utilisé,
        # on fait appel aux "mdproviders" pour peupler les méta-données.
        if identity:
            identity = Identity(identity) # dont show contents at print

            # allow IMetadataProvider plugins to scribble on the identity
            self.add_metadata(environ, classification, identity)

            # add the identity to the environment; a downstream
            # application can mutate it to do an 'identity reset'
            # as necessary, e.g. identity['login'] = 'foo',
            # identity['password'] = 'bar'
            environ['repoze.who.identity'] = identity
            # set the REMOTE_USER
            environ[self.remote_user_key] = userid

        # allow identifier plugins to replace the downstream
        # application (to do redirection and unauthorized themselves
        # mostly)
        app = environ.pop('repoze.who.application')
        if app is not self.app:
            logger and logger.info(
                'static downstream application replaced with %s' % app)

        wrapper = StartResponseWrapper(start_response)
        app_iter = app(environ, wrapper.wrap_start_response)

        # The challenge decider almost(?) always needs information from the
        # response.  The WSGI spec (PEP 333) states that a WSGI application
        # must call start_response by the iterable's first iteration.  If
        # start_response hasn't been called, we'll wrap it in a way that
        # triggers that call.
        if not wrapper.called:
            app_iter = wrap_generator(app_iter)

        if self.challenge_decider(environ, wrapper.status, wrapper.headers):
            logger and logger.info('challenge required')

            challenge_app = self.challenge(
                environ,
                classification,
                wrapper.status,
                wrapper.headers,
                identifier,
                identity
                )
            if challenge_app is not None:
                logger and logger.info('executing challenge app')
                if app_iter:
                    list(app_iter) # unwind the original app iterator
                # replace the downstream app with the challenge app
                app_iter = challenge_app(environ, start_response)
            else:
                logger and logger.info('configuration error: no challengers')
                raise RuntimeError('no challengers found')
        else:
            logger and logger.info('no challenge required')
            remember_headers = []
            if identifier:
                remember_headers = identifier.remember(environ, identity)
                if remember_headers:
                    logger and logger.info('remembering via headers from %s: %s'
                                           % (identifier, remember_headers))
            wrapper.finish_response(remember_headers)

        logger and logger.info(_ENDED % path_info)
        return app_iter

class VigiloAuthForgerMiddleware(AuthenticationForgerMiddleware):
    """
    Un middleware inspiré de
    C{repoze.who.plugins.testutil:AuthenticationForgerMiddleware}
    et qui simule le fonctionnement du middleware d'authentification.

    Ce middleware est destiné aux tests unitaires et permet également
    de simuler l'utilisation d'un mécanisme d'authentification externe
    avec Vigilo.
    """
    def __call__(self, environ, start_response):
        # Les tests unitaires peuvent définir cette variable
        # pour simuler l'utilisation d'un mécanisme d'authentification
        # externe. Par défaut, on utilise l'authentification interne.
        if 'vigilo.external_auth' not in environ:
            environ['vigilo.external_auth'] = False
        return super(VigiloAuthForgerMiddleware, self).__call__(
                    environ, start_response)


def _mk_mw_cfg(app, global_conf, config_file,
                log_file=None, log_level=None):
    """
    Inspiré par C{repoze.who.config:make_middleware_with_config}.
    """
    parser = WhoConfig(global_conf['here'])
    parser.parse(open(config_file))
    log_stream = None

    if log_file is not None:
        if log_file.lower() == 'stdout':
            log_stream = sys.stdout
        else:
            log_stream = open(log_file, 'wb')

    if log_level is None:
        log_level = logging.INFO
    else:
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

def make_middleware_with_config(app, global_conf, config_file, log_file=None,
                                log_level=None, skip_authentication=False):
    """
    Proxy :func:`repoze.who.config.make_middleware_with_config` to skip
    authentication when required.

    If  ``skip_authentication`` evaluates to ``True``, then the returned
    middleware will be an instance of :class:`AuthenticationForgerMiddleware`.

    Inspiré par C{repoze.who.plugins.testutil:make_middleware_with_config}.
    """
    if not asbool(skip_authentication):
        # We must not replace the middleware
        return _mk_mw_cfg(app, global_conf, config_file, log_file, log_level)

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
