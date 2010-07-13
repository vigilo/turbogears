# -*- coding: utf-8 -*-
"""Error controller"""

from tg import request, expose
from pylons.i18n import ugettext as _

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
        resp = request.environ.get('pylons.original_response')
        default_message = ("<p>" + _("We're sorry but we weren't "
                           "able to process this request.") + "</p>")
        if resp and resp.unicode_body:
            default_message = "<p>%s</p>" % resp.unicode_body
        values = dict(prefix=request.environ.get('SCRIPT_NAME', ''),
                      code=int(request.params.get('code', resp.status_int)),
                      message=request.params.get('message', default_message))
        return values

