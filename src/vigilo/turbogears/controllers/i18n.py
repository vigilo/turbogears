# -*- coding: utf-8 -*-
# Copyright (C) 2011-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce module contient un contrôleur pour TurboGears qui centralise
la gestion des méthodes relatives à l'authentification.

Les applications feront généralement hériter leur contrôleur
principal de celui-ci.
"""

import logging
import gettext
from tg.i18n import get_lang
from tg import response, expose
from pkg_resources import resource_filename, iter_entry_points
from vigilo.turbogears.controllers import BaseController

LOGGER = logging.getLogger(__name__)

class I18nController(BaseController):
    @expose()
    def i18n(self, **kw):
        """
        Renvoie les traductions de Vigilo au format JavaScript,
        utilisables ensuite par Babel dans le navigateur.
        """
        lang = get_lang() or 'en'

        # Charge et installe le fichier JS de traduction de chaque module
        translations = "babel.Translations.load("
        eps = sorted(iter_entry_points('vigilo.turbogears.i18n'),
                     key=lambda x: int(x.attrs[0]), reverse=True)
        for ep in eps:
            try:
                directory = resource_filename(ep.module_name, '')
                mofile = gettext.find(ep.name, directory, languages=lang)
                if mofile is None:
                    continue

                jsfile = mofile[:-3] + '.js'
                fhandle = open(jsfile, 'r')
                translations += fhandle.read()
                LOGGER.debug("Added JavaScript translations "
                             "for %(module)s (%(path)s)" % {
                                'module': ep.name,
                                'path': jsfile,
                            })
                fhandle.close()
                translations += ").load("
            except (ImportError, OSError):
                pass
        translations += "{}).install()"

        response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
        return translations
