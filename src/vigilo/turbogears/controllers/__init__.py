# -*- coding: utf-8 -*-
"""Contrôleurs communs à plusieurs applications."""

from tg import TGController, tmpl_context, request, i18n
from tg.render import render
from pylons.i18n import _, ungettext, N_
from tw.api import WidgetBunch

__all__ = ['Controller', 'BaseController']

old_set_temp_lang = i18n.set_temporary_lang
def set_temporary_lang(languages):
    import pylons
    from gettext import translation

    old_set_temp_lang(languages)
    t = translation('vigilo-turbogears', languages=languages, fallback=True)
    pylons.c.vigilo_turbogears = t
i18n.set_temporary_lang = set_temporary_lang


class BaseController(TGController):
    """
    Base class for the controllers in the application.

    Your web application should have one of these. The root of
    your application is used to compute URLs used by your app.

    """

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # TGController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']

        request.identity = request.environ.get('repoze.who.identity')
        tmpl_context.identity = request.identity
        return TGController.__call__(self, environ, start_response)

