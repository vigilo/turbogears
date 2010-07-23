# -*- coding: utf-8 -*-
"""
API d'interrogation des hôtes
"""

import tg
from tg import expose, request, validate
from tg.controllers import RestController
from tg.decorators import with_trailing_slash

from vigilo.models import tables
from vigilo.models.session import DBSession

from vigilo.turbogears.controllers.api import get_host, get_parent_id


class GraphsController(RestController):


    @with_trailing_slash
    @expose("api/graphs-all.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        idhost = get_parent_id("hosts")
        if idhost is not None:
            host = get_host(idhost)
            graphs = host.graphs
        else:
            graphs = DBSession.query(tables.Graph).all()
        result = []
        for graph in graphs:
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
        graph = DBSession.query(tables.Graph).get(idgraph)
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

