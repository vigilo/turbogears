# -*- coding: utf-8 -*-
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Contrôleurs communs à plusieurs applications."""

from tg import TGController, tmpl_context, request, i18n
from tg.render import render
from pylons.i18n import _, ungettext, N_
from tw.api import WidgetBunch
from pkg_resources import resource_filename

import pylons
from gettext import translation

__all__ = ['Controller', 'BaseController']

# Monkey-patching.
old_set_temp_lang = i18n.set_temporary_lang
def set_temporary_lang(languages):
    # Pour les locales de la forme "en_US",
    # on ajoute le langage (en) en fin de liste.
    # Voir aussi #651.
    languages.extend( [
        lang.split('_', 1)[0]
        for lang in languages
        if '_' in lang
    ] )

    # Pour les locales de la forme "en-us",
    # on ajoute le langage (en) en fin de liste.
    # Voir aussi #651.
    languages.extend( [
        lang.split('-', 1)[0]
        for lang in languages
        if '-' in lang
    ] )

    old_set_temp_lang(languages)

    # On récupère la langue définie par Pylons
    # (compromis entre les langues supportées par le navigateur
    # de l'utilisateur et celles supportées par l'application).
    # Durant les tests, l'attribut pylons_lang n'est pas défini,
    # on utilise "en" comme langue de repli.
    environ = pylons.request.environ
    lang = getattr(environ['pylons.pylons'].translator, 'pylons_lang', 'en')

    # On définit un traducteur pour vigilo-turbogears.
    tg_translator = translation('vigilo-turbogears',
        languages=lang, fallback=True)
    tg_translator.lang = lang
    pylons.c.vigilo_turbogears = tg_translator

    # Et un autre pour les thèmes.
    localedir = resource_filename('vigilo.themes.i18n', '')
    themes_translator = translation('vigilo-themes', localedir=localedir,
        languages=lang, fallback=True)
    themes_translator.lang = lang
    pylons.c.l_ = themes_translator
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
