# -*- coding: utf-8 -*-
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Module d'authentification par formulaire HTML gérant correctement
l'encodage des caractères.
"""

from zope.interface import implements
from repoze.who.interfaces import IChallenger, IIdentifier
from repoze.who.plugins.friendlyform import FriendlyFormPlugin as FFP

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
