# -*- coding: utf-8 -*-
"""
Bibliothèque de fonctions outils pour les applications utilisant TurboGears.
"""

import logging
import urllib2

import simplejson
from tg import request
from tg import url
from vigilo.models.tables import User

from pylons.i18n import ugettext as _

from vigilo.turbogears.units import convert_with_unit


__all__ = ('get_current_user', 'get_readable_metro_value', )

LOGGER = logging.getLogger(__name__)

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
    try:
        usage_req = get_through_proxy("rrdgraph", host, usage_url)
    except urllib2.HTTPError:
        logging.warning(_("Failed to get URL: %s") % url("/rrdgraph/%s/%s"
                                  % (host, usage_url),qualified=True))
        raise
    usage = simplejson.load(usage_req)['lastvalue']
    try:
        usage = float(usage)
        if ds.max is not None:
            percent = int(usage / float(ds.max) * 100)
        else:
            percent = None
        usage = convert_with_unit(usage)
    except (ValueError, TypeError):
        LOGGER.warning(_("Failed to convert DS %s on %s: "
                         "value was %s (max: %s)")
                          % (ds.name, host, usage, ds.max))
        usage = percent = None
    return (usage, percent)
