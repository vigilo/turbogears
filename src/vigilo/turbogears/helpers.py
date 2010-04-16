# -*- coding: utf-8 -*-
"""
Bibliothèque de fonctions outils pour les applications utilisant TurboGears.
"""

from tg import request
from vigilo.models.tables import User

__all__ = ('get_current_user', )

def get_current_user():
    """
    Renvoie l'instance de l'utilisateur actuellement connecté.
    
    @return: Instance correspondant à l'utilisateur actuellement connecté
        ou None s'il n'est pas identifié.
    @rtype: L{User} ou None
    """

    # Le plugin de méta-données SQLAlchemy (repoze.who.plugins.sa)
    # stocke directement l'instance de l'utilisateur dans l'identité.
    # Ce bout de code permet d'éviter une requête SQL supplémentaire.
    identity = request.environ.get('repoze.who.identity')
    if identity:
        user = identity.get('user')
        if user:
            return user

    # Pour les autres plugins.
    userid = request.identity.get('repoze.who.userid', None)
    if userid is None:
        return None
    return User.by_user_name(userid)

