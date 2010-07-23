# -*- coding: utf-8 -*-
"""
API d'interrogation des hôtes
"""

import pylons

import tg
from tg import expose, request, validate
from tg.decorators import with_trailing_slash
from tg.controllers import RestController
from tg.exceptions import HTTPNotFound

from vigilo.models import tables
from vigilo.models.session import DBSession

from vigilo.turbogears.controllers.api import get_host, get_pds, get_parent_id


class PerfDataSourcesController(RestController):


    @with_trailing_slash
    @expose("api/pds-all.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        idhost = get_parent_id("hosts")
        if idhost is None:
            raise HTTPNotFound("Can't find the host")
        host = get_host(idhost)
        result = []
        for pds in host.perfdatasources:
            result.append({
                "id": pds.idperfdatasource,
                "name": pds.name,
                "href": tg.url("/api/hosts/%s/perfdatasources/%s"
                               % (host.idhost, pds.idperfdatasource)),
                })
        return dict(perfdatasources=result)


    @expose("api/pds-one.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_one(self, idpds):
        idhost = get_parent_id("hosts")
        pds = get_pds(idpds, idhost)
        result = {
                "id": pds.idperfdatasource,
                "href": tg.url("/api/hosts/%s/perfdatasources/%s"
                               % (pds.host.idhost, pds.idperfdatasource)),
                "host": {
                    "id": pds.host.idhost,
                    "name": pds.host.name,
                    "href": tg.url("/api/hosts/%s" % pds.host.idhost),
                    },
                "name": pds.name,
                "type": pds.type,
                "label": pds.label,
                "factor": pds.factor,
                "max": pds.max,
                }
        graphs = []
        for graph in pds.graphs:
            graphs.append({
                "id": graph.idgraph,
                "href": tg.url("/api/graphs/%s" % graph.idgraph),
                "name": graph.name,
                })
        result["graphs"] = graphs
        return dict(pds=result)
