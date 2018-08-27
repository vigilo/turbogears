# -*- coding: utf-8 -*-
# Copyright (C) 2011-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Contient la fonction de classement des requêtes HTTP.

Trois types de requêtes sont actuellement définis:
- "vigilo-api" : pour les requêtes concernant l'API de Vigilo.
- "browser-external" :  pour les requêtes faites par un navigateur HTTP
                        et ayant fait l'objet d'une authentification par
                        un mécanisme externe (ex: Kerberos).
- "browser" :           pour les autres requêtes faites par un navigateur.
"""

import zope.interface
from repoze.who.interfaces import IRequestClassifier
from repoze.who.classifiers import default_request_classifier

def vigilo_classifier(environ):
    if '/api/' in environ.get('PATH_INFO', ''):
        return 'vigilo-api'

    # Si la requête provient de 127.0.0.1, on utilise une classification
    # spéciale qui permettra d'identifier cette connexion comme étant interne.
    # Note : dans le cas où un reverse proxy est utilisé, l'adresse IP source
    #        peut être incorrecte. Cette classification ne doit alors pas être
    #        utilisée.
    if environ.get('REMOTE_ADDR') in ('127.0.0.1', '::1'):
        return 'internal'

    # Sinon, on s'en remet au classifier par défaut (qui identifie
    # le type "browser" correspondant à une requête de navigateur HTTP).
    default = default_request_classifier(environ)

    # S'il s'agit d'une requête de navigateur et qu'une authentification
    # externe a été utilisée, on l'indique ici.
    remote_user_key = environ.get('repoze.who.remote_user_key')
    if default == 'browser' and remote_user_key and environ.get(remote_user_key):
        return 'browser-external'
    return default

zope.interface.directlyProvides(vigilo_classifier, IRequestClassifier)
