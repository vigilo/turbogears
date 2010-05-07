# -*- coding: utf-8 -*-
"""
Bibliothèque de fonctions outils pour les applications utilisant TurboGears.
"""

from tg import request
from tg import url
import logging
from vigilo.models.tables import User

from pylons.i18n import ugettext as _

from vigilo.turbogears.units import convert_with_unit


__all__ = ('get_current_user', 'get_readable_metro_value', )

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

def get_readable_metro_value(host, ds):
    """
    Récupère et retourne une valeur "lisible" de métrologie, c'est à dire avec
    trois chiffres significatifs et l'ordre de grandeur.

    @param host: le nom d'hôte
    @type  host: C{str}
    @param ds: l'indicateur de métrologie
    @type  ds: L{vigilo.models.tables.perfdatasource}
    @return: un couple valeur entière, valeur en pourcentage 
    @rtype:  C{tuple}
    """
    # doit être chargé après
    from vigilo.turbogears.controllers.proxy import get_through_proxy

    usage_url = "lastvalue?host=%s&ds=%s" % (host, ds.name)
    usage_req = get_through_proxy("rrdgraph", host, usage_url)
    usage = usage_req.read()
    try:
        usage = float(usage)
        percent = int(usage / float(ds.max) * 100)
        usage = convert_with_unit(usage)
    except (ValueError, TypeError):
        usage = "?"
        percent = "?"
        logging.warning(_("Failed to get URL: %s") % url("/rrdgraph/%s/%s"
                                  % (host, usage_url),qualified=True))
    return (usage, percent)
