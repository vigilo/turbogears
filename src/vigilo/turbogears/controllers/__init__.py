# -*- coding: utf-8 -*-
# Copyright (C) 2006-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Contrôleurs communs à plusieurs applications."""
from __future__ import absolute_import
from io import UnsupportedOperation
from tg import tmpl_context, request, controllers
from tg.render import render
from tg.i18n import ugettext as _, ungettext, gettext_noop as N_, \
    LanguageError, get_lang, add_fallback
from pkg_resources import resource_filename

from gettext import translation

__all__ = ['BaseController']

class Package(object):
    def __init__(self, pkg):
        self._name = pkg

    def __getattr__(self, attr):
        if attr is '__name__':
            return self._name

class BaseController(controllers.TGController):
    """
    Base class for the controllers in the application.

    Your web application should have one of these. The root of
    your application is used to compute URLs used by your app.

    """
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # TGController.__call__ dispatches to the Controller method
        # the request is routed to.
        request.identity = request.environ.get('repoze.who.identity')
        tmpl_context.identity = request.identity
        try:
            # On tente de réinitialiser la position dans le corps de la requête.
            # Nécessaire car le corps peut avoir déjà été consommé lorsque
            # WebOb tente de le consommer à nouveau, ce qui conduit
            # à une exception webob.request.DisconnectionError
            environ['wsgi.input'].seek(0)
        except (UnsupportedOperation, AttributeError):
            pass
        return super(BaseController, self).__call__(environ, start_response)

    def _get_routing_info(self, url=None):
        """
        Récupère les informations de routage relatives à l'URL donnée
        ou à l'URL stockée dans la requête courante si aucune URL n'est
        passée explicitement à la fonction.

        Par rapport à la méthode parente, cette version supprime
        le préfixe "/" de l'URL passée en argument, pour corriger un bug
        rencontré sous CentOS 7 avec la méthode _find_object() de TurboGears.
        """
        if url is not None:
            url = url.lstrip('/')
        return super(BaseController, self)._get_routing_info(url)

    def _before(self, *remainder, **params):
        transl = (
            ('vigilo-turbogears', None),
            ('vigilo-themes', resource_filename('vigilo.themes.i18n', '')),
            ('vigilo-models', None),
            ('vigilo-common', None),
        )

        lang = get_lang() or 'en'
        for pkg, localedir in transl:
            try:
                add_fallback(lang, tg_config={'localedir': localedir,
                                              'package': Package(pkg)})
            except LanguageError:
                pass
