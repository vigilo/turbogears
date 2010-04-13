# -*- coding: utf-8 -*-

from tg import request
from vigilo.models.tables import User

__all__ = ('get_current_user', )

def get_current_user():
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

