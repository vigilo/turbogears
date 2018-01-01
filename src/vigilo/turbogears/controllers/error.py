# -*- coding: utf-8 -*-
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Error controller"""

import re
from tg import request, expose
from tg.i18n import ugettext as _

__all__ = ['ErrorController']

# pylint: disable-msg=R0201
class ErrorController(object):
    """
    Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """

    @expose('error.html')
    def document(self, *args, **kwargs):
        """Render the error document"""
        resp = request.environ.get('tg.original_response')
        default_message = _("We're sorry but we weren't "
                           "able to process this request.")
        if resp and resp.unicode_body:
            # WebError encode automatiquement les caractères spéciaux
            # sous forme d'entités (numériques ou nommées).
            # On doit les décoder pour éviter un double encodage au
            # niveau du template (Cf. ticket #191).
            def repl(match):
                entities = {
                    'amp': '&',
                    'gt': '>',
                    'lt': '<',
                    'quot': '"',
                    'apos': "'",
                }

                try:
                    # On suppose qu'il s'agit d'une entité numérique.
                    return unichr(int(str(match.group(2)), 10))
                except ValueError:
                    # Il ne s'agit probablement pas d'une entité numérique,
                    # on tente une conversion avec les entités de base de XML.
                    # Si cela échoue également, on renvoie le texte initial.
                    return entities.get(
                        str(match.group(1)),
                        str(match.group(0)))

            default_message = re.sub(
                u'&(#([0-9]+)|amp|quot|lt|gt);',
                repl, resp.unicode_body)
        values = dict(prefix=request.environ.get('SCRIPT_NAME', ''),
                      code=int(request.params.get('code', resp.status_int)),
                      message=request.params.get('message', default_message))
        return values
