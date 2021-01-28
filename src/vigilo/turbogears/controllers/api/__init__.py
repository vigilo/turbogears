# -*- coding: utf-8 -*-
# Copyright (C) 2006-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce module contient des fonctions utilisées par les contrôlleurs de l'API
"""

import urlparse

import tg
from tg.exceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden
from sqlalchemy.sql.expression import or_

from vigilo.models import tables
from vigilo.models.session import DBSession
from vigilo.turbogears.helpers import get_current_user


def get_parent_id(obj_type=None):
    """
    Retourne l'ID de l'objet parent dans l'URL, avec une vérification
    optionnelle sur le type.

    @param obj_type: type d'élément à retourner, tel qu'il apparaît dans l'URL
    @type  obj_type: C{str}
    """
    url = urlparse.urlparse(tg.request.url)
    url_path = url.path.replace(tg.url("/api/"),"")
    url_array = url_path.split("/")
    if len(url_array) < 4:
        return None
    if obj_type is not None and url_array[-4] != obj_type:
        msg = "Expected object type %(exp)s and got type %(got)s %(num)s" \
              % {"exp": obj_type, "got": url_array[-4], "num": len(url_array)}
        raise HTTPBadRequest(msg)
    return url_array[-3]

def get_all_hosts():
    """
    Retourne tous les hôtes (C{tables.Host}) auxquels l'utilisateur à accès
    """
    user = get_current_user()
    if not user:
        raise HTTPForbidden("You must be logged in")
    hostgroup = tables.secondary_tables.SUPITEM_GROUP_TABLE.alias()
    servicegroup = tables.secondary_tables.SUPITEM_GROUP_TABLE.alias()
    hosts = DBSession.query(tables.Host).distinct().outerjoin(
            (hostgroup, hostgroup.c.idsupitem == tables.Host.idhost),
            (tables.LowLevelService,
                tables.LowLevelService.idhost == tables.Host.idhost),
            (servicegroup,
                servicegroup.c.idsupitem == tables.LowLevelService.idservice),
        )
    # ACLs
    if not tg.config.is_manager.is_met(tg.request.environ):
        user_groups = [ug[0] for ug in user.supitemgroups() if ug[1]]
        if not user_groups:
            return []
        hosts = hosts.filter(or_(
            hostgroup.c.idgroup.in_(user_groups),
            servicegroup.c.idgroup.in_(user_groups),
        ))
    return hosts.all()

def get_host(idhost):
    """
    Retourne un hôte (C{tables.Host}) à partir de son ID ou de son nom

    @param idhost: l'identifiant de l'hôte
    @type  idhost: C{int} ou C{str}
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

def get_all_services(model_class):
    """
    Retourne tous les services auxquels l'utilisateur à accès, suivant le type
    demandé en argument.

    @param model_class: la classe du modèle correspondante au type de service
        demandé
    @type  model_class: sous-classe de C{tables.Service}
    """
    user = get_current_user()
    if not user:
        raise HTTPForbidden("You must be logged in")
    services = DBSession.query(model_class)
    # ACLs
    # Rappel :  il n'y a pas de permission spécifique
    #           donnant accès aux services de haut niveau.
    if model_class is tables.LowLevelService and \
        not tg.config.is_manager.is_met(tg.request.environ):
        services = services.join(
                (tables.UserSupItem,
                    tables.UserSupItem.idsupitem == model_class.idsupitem)
            )
    return services.all()

def get_service(idservice, service_type, idhost=None):
    """
    Retourne un service à partir de son ID ou de son nom. Si le service est un
    service de bas niveau (C{tables.LowLevelService}), il faut aussi fournir un
    identifiant d'hôte (ID ou nom).

    @param idservice: l'identifiant du service à récupérer, ou son nom
    @type  idservice: C{int} ou C{str}
    @param service_type: le type de service à récupérer
    @type  service_type: C{str}: C{lls} ou C{hls}
    @param idhost: l'identifiant de l'hôte associé au service, ou son nom
    @type  idhost: C{int} ou C{str}
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
    if not service.is_allowed_for(user):
        raise HTTPForbidden("Access to this service is forbidden")
    return service

def get_pds(idpds, idhost=None):
    """
    Retourne un indicateur de performance (C{tables.PerfDataSource}) à partir
    de son ID ou de son nom. Si seul le nom est fourni, il faut aussi préciser
    un hôte sur lequel est hébergé cette donnée.

    @param idpds: identifiant de la donnée de perf, ou son nom
    @type  idpds: C{int} ou C{str}
    @param idhost: l'identifiant de l'hôte associé à la donnée de perf, ou son
        nom
    @type  idhost: C{int} ou C{str}
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

def check_map_access(m):
    """
    Vérifie que l'utilisateur courant a bien accès à la carte donnée en
    argument

    @param m: carte à tester
    @type  m: C{tables.Map}
    """
    user = get_current_user()
    if not user:
        raise HTTPForbidden("You must be logged in")
    allowed_mapgroups = user.mapgroups(only_id=True, only_direct=True)
    for mapgroup in m.groups:
        if mapgroup.idgroup in allowed_mapgroups:
            return True
    raise HTTPForbidden("Access denied to map %s" % m.idmap)

