# -*- coding: utf-8 -*-
# Copyright (C) 2006-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Bibliothèque de fonctions outils pour les applications utilisant TurboGears.
"""

import logging
import urllib2

try:
    import simplejson as json
except ImportError:
    import json

from tg import request, url
from tg.i18n import ugettext as _
from vigilo.models.tables import User
import pkg_resources

from vigilo.turbogears.units import convert_with_unit
from vigilo.models.session import DBSession
from vigilo.models import tables


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

def get_locales(modname):
    try:
        locales = pkg_resources.resource_listdir(modname, 'i18n')
    except ImportError:
        return []
    else:
        # On ne garde que les dossiers non cachés.
        locales = [
            locale for locale in locales
            if pkg_resources.resource_isdir(modname, 'i18n/%s' % locale)
            and not locale.startswith('.')
        ]
        return locales

def get_readable_metro_value(pds):
    """
    Récupère et retourne une valeur "lisible" de métrologie, c'est à dire avec
    trois chiffres significatifs et l'ordre de grandeur.

    @param pds: l'indicateur de métrologie
    @type  pds: C{vigilo.models.tables.perfdatasource.PerfDataSource}
    @return: un couple valeur entière, valeur en pourcentage
    @rtype:  C{tuple}
    """
    # doit être chargé après
    from vigilo.turbogears.controllers.proxy import get_through_proxy

    host = pds.host.name
    usage_url = "lastvalue?host=%s&ds=%s" % (
        urllib2.quote(host, ''),
        urllib2.quote(pds.name, ''),
    )
    try:
        usage_req = get_through_proxy("vigirrd", host, usage_url)
    except urllib2.HTTPError:
        logging.warning("Failed to get URL: %s",
                        url("/vigirrd/%s/%s" % (host, usage_url),
                        qualified=True))
        raise
    usage = json.load(usage_req)['lastvalue']
    try:
        usage = float(usage)
        if pds.max is not None:
            percent = int(usage / float(pds.max) * 100)
        else:
            percent = None
        usage = convert_with_unit(usage)
    except (ValueError, TypeError):
        LOGGER.warning("Failed to convert DS %(ds)s on %(host)s: "
                         "value was %(value)s (max: %(max)s)", {
                            'ds': pds.name,
                            'host': host,
                            'value': usage,
                            'max': pds.max,
                         })
        usage = percent = None
    return (usage, percent)

def describe_supitem(idsupitem):
    """
    Retourne une description humaine d'un objet supervisé.

    @param idsupitem: Identifiant de l'objet supervisé.
    @type idsupitem: C{int}
    @return: Description humaine, dans la langue de l'utilisateur.
    @rtype: C{unicode}
    """
    supitem = DBSession.query(tables.SupItem).get(idsupitem)
    if isinstance(supitem, tables.HighLevelService):
        return _('high-level service "%s"') % supitem.servicename
    if isinstance(supitem, tables.Host):
        return _('host "%s"') % supitem.name
    if isinstance(supitem, tables.LowLevelService):
        return _('service "%(service)s" on host "%(host)s"') % {
            'host': supitem.host.name,
            'service': supitem.servicename,
        }
    raise ValueError('Invalid argument')
