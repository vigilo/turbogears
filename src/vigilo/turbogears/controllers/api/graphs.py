# -*- coding: utf-8 -*-
"""
API d'interrogation des hôtes
"""


import tg
from tg import expose
from tg.controllers import RestController
from tg.decorators import with_trailing_slash
from tg.exceptions import HTTPNotFound, HTTPForbidden

from vigilo.models import tables
from vigilo.models.session import DBSession

from vigilo.turbogears.helpers import get_current_user
from vigilo.turbogears.controllers.api import get_all_hosts, get_host, \
                                              get_parent_id


class GraphsController(RestController):
    """
    Récupération des L{Graph<tables.Graph>}es.  Ce contrôlleur peut être monté
    soit à la racine soit sous un hôte.
    """

    # Messages PyLint qu'on supprime
    # - R0201: method could be a function: c'est le fonctionnement du
    #   RestController
    # - C0111: missing docstring: les fonctions get_all et get_one sont
    #   définies dans le RestController

    @with_trailing_slash
    @expose("api/graphs-all.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        # pylint:disable-msg=C0111,R0201
        idhost = get_parent_id("hosts")
        if idhost is not None:
            hosts = [get_host(idhost), ]
        else:
            hosts = get_all_hosts()
        result = []
        for host in hosts:
            for graph in host.graphs:
                result.append({
                        "id": graph.idgraph,
                        "href": tg.url("/api/graphs/%s" % graph.idgraph),
                        "name": graph.name,
                        })
        return dict(graphs=result)


    @expose("api/graphs-one.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_one(self, idgraph):
        # pylint:disable-msg=C0111,R0201
        graph = DBSession.query(tables.Graph).get(idgraph)
        if not graph:
            raise HTTPNotFound("Can't find graph %s" % idgraph)
        # ACLs
        user = get_current_user()
        #user = tables.User.by_user_name(u"editor") # debug
        for pds in graph.perfdatasources:
            if not pds.host.is_allowed_for(user):
                raise HTTPForbidden("Access denied to graphs on host %s"
                                    % pds.host.name)
        result = {"id": graph.idgraph,
                  "href": tg.url("/api/graphs/%s" % graph.idgraph),
                  "name": graph.name,
                  "template": graph.template,
                  "vlabel": graph.vlabel,
                  }
        groups = []
        for group in graph.groups:
            groups.append({
                "id": group.idgroup,
                "name": group.name,
                "href": tg.url("/api/graphgroups/%s" % group.idgroup),
                })
        result["groups"] = groups
        datasources = []
        for pds in graph.perfdatasources:
            datasources.append({
                "id": pds.idperfdatasource,
                "name": pds.name,
                "href": tg.url("/api/host/%s/perfdatasources/%s"
                               % (pds.idhost, pds.idperfdatasource)),
                })
        result["perfdatasources"] = datasources
        return dict(graph=result)

