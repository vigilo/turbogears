# -*- coding: utf-8 -*-
"""
Ce module contient des fonctions utilisées par les contrôlleurs de l'API
"""

import urlparse

import tg
from tg.exceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden

from vigilo.models import tables
from vigilo.models.session import DBSession
from vigilo.turbogears.helpers import get_current_user


def get_parent_id(obj_type=None):
    """
    Retourne l'ID de l'objet parent dans l'URL
    """
    url = urlparse.urlparse(tg.request.url)
    url_path = url.path.replace(tg.url("/api/"),"")
    url_array = url_path.split("/")
    if len(url_array) < 4:
        return None
    if obj_type is not None and url_array[-4] != obj_type:
        raise HTTPBadRequest("Expected object type %(exp)s and got type %(got)s %(num)s"
                % {"exp": obj_type, "got": url_array[-4], "num": len(url_array)})
    return url_array[-3]

def get_host(idhost):
    """
    Retourne un L{tables.Host} à partir de son ID ou de son nom
    """
    try:
        idhost = int(idhost)
    except ValueError:
        host = tables.Host.by_host_name(idhost)
    else:
        host = DBSession.query(tables.Host).get(idhost)
    if host is None:
        raise HTTPNotFound("Can't find the host: %s" % idhost)
    # ACLs
    user = get_current_user()
    if not user:
        raise HTTPForbidden("You must be logged in")
    if not host.is_allowed_for(user):
        raise HTTPForbidden("Access to this host is forbidden")
    return host

def get_service(idservice, service_type, idhost=None):
    """
    Retourne un service à partir de son ID ou de son nom. Si le service est un
    L{tables.LowLevelService}, il faut aussi fournir un identifiant d'hôte (ID
    ou nom).
    """
    try:
        idservice = int(idservice)
    except ValueError:
        # on a reçu un nom de service
        if service_type == "lls":
            if idhost is None:
                raise HTTPNotFound("Can't find the host, you must use "
                                   "the numeric service ID")
            host = get_host(idhost)
            service = tables.LowLevelService.by_host_service_name(
                                        host.name, idservice)
        elif service_type == "hls":
            service = tables.HighLevelService.by_service_name(idservice)
    else:
        service = DBSession.query(tables.Service).get(idservice)
    if service is None:
        raise HTTPNotFound("Can't find the service: %s" % idservice)
    # ACLs
    user = get_current_user()
    if not user:
        raise HTTPForbidden("You must be logged in")
    if not serivce.is_allowed_for(user):
        raise HTTPForbidden("Access to this service is forbidden")
    return service

def get_pds(idpds, idhost=None):
    """
    Retourne une L{tables.PerfDataSource} à partir de son ID ou de son nom. Si
    seul le nom est fourni, il faut aussi préciser un hôte sur lequel est
    hébergé cette donnée.
    """
    try:
        idpds = int(idpds)
    except ValueError:
        # on a reçu un nom de PDS
        if idhost is None:
            raise HTTPNotFound("Can't find the host, you must use "
                               "the numeric service ID")
        host = get_host(idhost) # pour avoir la traduction des noms en id
        pds = tables.PerfDataSource.by_host_and_source_name(host.idhost, idpds)
    else:
        pds = DBSession.query(tables.PerfDataSource).get(idpds)
    if pds is None:
        raise HTTPNotFound("Can't find the perf data source: %s" % idpds)
    return pds
