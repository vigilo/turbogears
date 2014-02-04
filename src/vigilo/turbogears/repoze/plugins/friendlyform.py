# -*- coding: utf-8 -*-
# Copyright (C) 2006-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Module d'authentification par formulaire HTML gérant correctement
l'encodage des caractères.
"""

from zope.interface import implements
from repoze.who.interfaces import IChallenger, IIdentifier
from repoze.who.plugins.friendlyform import FriendlyFormPlugin as FFP
from paste.httpexceptions import HTTPFound, HTTPException
from paste.response import remove_header, replace_header
from paste.httpheaders import CACHE_CONTROL

class HTTPFoundGrabFragment(HTTPException):
    """
    Une exception qui redirige l'utilisateur vers une autre page
    (à la manière de HTTPFound), mais mais qui permet de récupérer
    le fragment saisi par l'utilisateur dans la requête originale
    avant d'effectuer la redirection.
    """
    code = 200
    title = 'Redirecting to the login page...'
    # Si JavaScript est activé, un script récupère le fragment
    # et redirige l'utilisateur vers le formulaire d'authentification
    # en propageant cette information.
    # NB: on ne peut pas utiliser window.location.hash à cause
    # d'un bug dans Firefox (la valeur du hash est URI-décodée
    # lors d'une lecture de l'attribut; elle ne devrait pas).
    #
    # Si JavaScript est désactivé, lien permet à l'utilisateur d'accéder
    # manuellement au formulaire. Dans ce cas, le fragment sera perdu.
    template = '''\
        <script type="text/javascript">
            var hash = window.location.href.split("#")[1] || "";
            if (hash != '') hash = '#' + hash;
            var loc = '%(detail)s' + encodeURIComponent(hash) + hash;
            window.location = loc;
        </script>

        <a href="%(detail)s">Click here</a> if you're not redirected
            within 5 seconds.
    '''

    def __init__(self, location, headers=None):
        if headers is None:
            headers = []
        elif not isinstance(headers, list):
            # Les en-têtes ont été créés à l'aide de WebOb.
            # On supprime la taille du corps de la page car elle valait
            # zéro (il s'agissait d'une redirection), mais ce n'est plus
            # le cas à présent (et Paste vérifie cette valeur).
            headers.pop('Content-Length', None)
            # Conversion du format de WebOb vers le format de Paste.
            headers = headers.items()
        # Supprime la redirection.
        remove_header(headers, 'location')
        # Empêche la mise en cache de la page intermédiaire.
        CACHE_CONTROL.apply(headers, no_cache=True, no_store=True)
        super(HTTPFoundGrabFragment, self).__init__(location, headers)


class FriendlyFormPlugin(FFP):
    """
    Une classe dérivée de L{repoze.who.plugins.friendlyform:FriendlyFormPlugin}
    mais qui ajoute en plus le support d'un encodage pour les valeurs du
    formulaire.

    Cet encodage est utilisé pour décoder le contenu du formulaire
    d'authentification. Les valeurs qui composent "l'identité" de l'utilisateur
    dans l'environnement de la requête WSGI sont systématiquement de l'Unicode
    (via le type natif de Python) si un encodage a été fourni en paramètre
    à l'initialiseur de cette classe.
    """

    implements(IChallenger, IIdentifier)

    def __init__(self, login_form_url, login_handler_path, post_login_url,
                 logout_handler_path, post_logout_url, rememberer_name,
                 login_counter_name=None, encoding=None):
        """
        :param login_form_url: The URL/path where the login form is located.
        :type login_form_url: str
        :param login_handler_path: The URL/path where the login form is
            submitted to (where it is processed by this plugin).
        :type login_handler_path: str
        :param post_login_url: The URL/path where the user should be redirected
            to after login (even if wrong credentials were provided).
        :type post_login_url: str
        :param logout_handler_path: The URL/path where the user is logged out.
        :type logout_handler_path: str
        :param post_logout_url: The URL/path where the user should be
            redirected to after logout.
        :type post_logout_url: str
        :param rememberer_name: The name of the repoze.who identifier which
            acts as rememberer.
        :type rememberer_name: str
        :param login_counter_name: The name of the query string variable which
            will represent the login counter.
        :type login_counter_name: str
        :param encoding: Name of the encoding the form values are encoded with.
        :type encoding: str

        The login counter variable's name will be set to ``__logins`` if
        ``login_counter_name`` equals None.
        """
        super(FriendlyFormPlugin, self).__init__(
            login_form_url=login_form_url,
            login_handler_path=login_handler_path,
            post_login_url=post_login_url,
            logout_handler_path=logout_handler_path,
            post_logout_url=post_logout_url,
            rememberer_name=rememberer_name,
            login_counter_name=login_counter_name
        )
        self.encoding = encoding

    # IIdentifier
    def identify(self, environ):
        """
        Ajoute le support de l'encodage des valeurs du formulaire en plus
        des fonctionnalités déjà fournies dans la classe mère.
        """
        res = super(FriendlyFormPlugin, self).identify(environ)

        # Si la classe mère a réussi à identifier l'utilisateur,
        # on doit décoder les valeurs avec l'encodage fourni.
        if isinstance(res, dict) and isinstance(self.encoding, basestring):
            for key in res.keys():
                if not isinstance(res[key], unicode):
                    res[key] = res[key].decode(self.encoding)

        return res

    # IChallenger
    def challenge(self, environ, status, app_headers, forget_headers):
        res = super(FriendlyFormPlugin, self).challenge(
            environ, status, app_headers, forget_headers)

        # Si le challenger s'apprête à nous rediriger vers le formulaire
        # d'authentification, on affiche une page web à la place qui va
        # récupérer l'éventuel fragment de l'URL et le propager.
        if isinstance(res, HTTPFound):
            # L'API de Paste a changé entre les versions.
            if isinstance(res.location, basestring):
                location = res.location # 1.7.4+
            else:
                location = res.location() # 1.7.2

            # Si on s'apprête à rediriger l'utilisateur vers le formulaire
            # d'authentification, on retourne une page intermédiaire à la
            # place qui permet de sauvegarder le fragment de l'URL courante
            # avant de rediriger l'utilisateur vers le formulaire.
            # Le fragment sera ensuite propagé vers la page "post_login_url".
            login_form_url = self._get_full_path(self.login_form_url, environ)
            if location.partition('?')[0] == login_form_url and \
                'repoze.who.logins' not in environ:
                return HTTPFoundGrabFragment(location, res.headers)
        return res
