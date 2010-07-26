# -*- coding: utf-8 -*-
"""
Bibliothèque de fonctions outils pour les applications utilisant TurboGears.
"""

import logging
import urllib2
import pylons

import simplejson
from tg import request, url
from vigilo.models.tables import User

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
    if request.identity is None:
        return None
    userid = request.identity.get('repoze.who.userid', None)
    if userid is None:
        return None
    return User.by_user_name(userid)

def get_readable_metro_value(pds):
    """
    Récupère et retourne une valeur "lisible" de métrologie, c'est à dire avec
    trois chiffres significatifs et l'ordre de grandeur.

    @param pds: l'indicateur de métrologie
    @type  pds: L{vigilo.models.tables.perfdatasource.PerfDataSource}
    @return: un couple valeur entière, valeur en pourcentage 
    @rtype:  C{tuple}
    """
    # doit être chargé après
    from vigilo.turbogears.controllers.proxy import get_through_proxy

    host = pds.host.name
    usage_url = "lastvalue?host=%s&ds=%s" % (host, pds.name)
    try:
        usage_req = get_through_proxy("rrdgraph", host, usage_url)
    except urllib2.HTTPError:
        logging.warning(_("Failed to get URL: %s"),
                        url("/rrdgraph/%s/%s" % (host, usage_url),
                        qualified=True))
        raise
    usage = simplejson.load(usage_req)['lastvalue']
    try:
        usage = float(usage)
        if pds.max is not None:
            percent = int(usage / float(pds.max) * 100)
        else:
            percent = None
        usage = convert_with_unit(usage)
    except (ValueError, TypeError):
        LOGGER.warning(_("Failed to convert DS %(ds)s on %(host)s: "
                         "value was %(value)s (max: %(max)s)"), {
                            'ds': pds.name,
                            'host': host,
                            'value': usage,
                            'max': pds.max,
                         })
        usage = percent = None
    return (usage, percent)

def ugettext(message):
    return pylons.c.vigilo_turbogears.ugettext(message)

def lazy_ugettext(message):
    return pylons.c.vigilo_turbogears.lazy_ugettext(message)
_ = ugettext

