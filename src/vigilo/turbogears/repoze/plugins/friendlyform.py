# -*- coding: utf-8 -*-
# Copyright (C) 2006-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Module d'authentification par formulaire HTML gérant correctement
l'encodage des caractères.
"""

from repoze.who.interfaces import IChallenger, IIdentifier
from string import Template
from tg.configuration.auth.fastform import FastFormPlugin as FFP
from tg.controllers.util import _build_url
from webob.exc import HTTPFound, WSGIHTTPException
from zope.interface import implementer


class HTTPGrabFragment(WSGIHTTPException):
    """
    Une exception qui redirige l'utilisateur vers une autre page
    (à la manière de HTTPFound), mais qui permet de récupérer
    le fragment saisi par l'utilisateur dans la requête originale
    avant d'effectuer la redirection.
    """
    code = 200
    title = 'Redirecting to the login page...'

    # Si JavaScript est activé, un script récupère le fragment
    # et redirige l'utilisateur vers le formulaire d'authentification
    # en propageant cette information.
    #
    # NB: on ne peut pas utiliser window.location.hash à cause
    # d'un bug dans Firefox (la valeur du hash est URI-décodée
    # lors d'une lecture de l'attribut; elle ne devrait pas).
    #
    # Si JavaScript est désactivé, un lien permet à l'utilisateur d'accéder
    # manuellement au formulaire. Dans ce cas, le fragment sera perdu.
    body_template_obj = Template('''\
        <script type="text/javascript">
            var hash = window.location.href.split("#")[1] || "";
            if (hash != '') hash = '#' + hash;
            var loc = '${detail}' + encodeURIComponent(hash) + hash;
            window.location = loc;
        </script>

        <a href="${detail}">Click here</a> if you're not redirected
            within 5 seconds.
    ''')

    def __init__(self, location, headers=None):
        super(HTTPGrabFragment, self).__init__(location, headers)

        # Empêche la mise en cache de la page intermédiaire.
        self.cache_expires = True


@implementer(IChallenger, IIdentifier)
class FriendlyFormPlugin(FFP):
    """
    Classe dérivée de L{tg.configuration.auth.fastform:FastFormPlugin} qui
    ajoute en plus:

    * Un message de logging lorsque l'utilisateur se déconnecte.
    * Un mécanisme permettant de propager le fragment de la requête d'origine
      après l'authentification.
    """

    def _fix_prefix(self, environ, url):
        script_name = environ['SCRIPT_NAME'].rstrip('/')
        if url.startswith(script_name):
            url = url[len(script_name):]
        return url

    # IChallenger
    def challenge(self, environ, status, app_headers, forget_headers):
        path_info = environ['PATH_INFO']

        # Configuring the headers to be set:
        cookies = [(h,v) for (h,v) in app_headers if h.lower() == 'set-cookie']
        headers = forget_headers + cookies

        if path_info == self.logout_handler_path:
            logger = environ.get('repoze.who.logger')
            logger and logger.info(
                'User "%(login)s" (%(fullname)s) logged out (from %(ip)s)', {
                'login': environ['repoze.who.identity']['repoze.who.userid'],
                'fullname': environ['repoze.who.identity']['fullname'],
                'ip': environ.get('REMOTE_ADDR') or '0.0.0.0',
            })

            params = {}
            if 'came_from' in environ:
                # @HACK The plugin uses _build_url() in identify() to set environ['came_from'],
                #       which adds the installation prefix automatically, but the application
                #       calls redirect() which already adds it. Remove the duplicate here.
                params.update({'came_from': self._fix_prefix(environ, environ['came_from'])})
            destination = _build_url(environ, self.post_logout_url, params=params)
            return HTTPFound(location=destination, headers=headers)

        came_from = _build_url(environ, path_info)
        # @HACK _build_url() adds the installation prefix to the URL automatically,
        #       but it is already present in this case. Remove the duplicate here.
        params = {'came_from': self._fix_prefix(environ, came_from)}

        destination = _build_url(environ, self.login_form_url, params=params)
        return HTTPGrabFragment(location=destination, headers=headers)
