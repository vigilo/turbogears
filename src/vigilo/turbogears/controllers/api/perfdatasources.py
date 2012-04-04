# -*- coding: utf-8 -*-
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
API d'interrogation des hôtes
"""


import tg
from tg import expose
from tg.decorators import with_trailing_slash
from tg.controllers import RestController
from tg.exceptions import HTTPNotFound

#from vigilo.models import tables
#from vigilo.models.session import DBSession

from vigilo.turbogears.controllers.api import get_host, get_pds, get_parent_id


class PerfDataSourcesV1(RestController):
    """
    Controlleur d'accès aux données de performances d'un hôte. Ne peut être
    monté qu'après un hôte dans l'arborescence. Techniquement on pourrait aussi
    le monter à la racine, mais il faudrait alors limiter le nombre de
    résultats pour éviter de saturer la machine. On fera s'il y a besoin.
    """

    # Messages PyLint qu'on supprime
    # - R0201: method could be a function: c'est le fonctionnement du
    #   RestController
    # - C0111: missing docstring: les fonctions get_all et get_one sont
    #   définies dans le RestController

    apiver = 1


    @with_trailing_slash
    @expose("api/pds-all.xml", content_type="application/xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        # pylint:disable-msg=C0111,R0201
        idhost = get_parent_id("hosts")
        if idhost is None:
            raise HTTPNotFound("Can't find the host")
        host = get_host(idhost)
        result = []
        for pds in host.perfdatasources:
            result.append({
                "id": pds.idperfdatasource,
                "name": pds.name,
                "href": tg.url("/api/v%s/hosts/%s/perfdatasources/%s"
                           % (self.apiver, host.idhost, pds.idperfdatasource)),
                })
        return dict(perfdatasources=result)


    @expose("api/pds-one.xml", content_type="application/xml; charset=utf-8")
    @expose("json")
    def get_one(self, idpds):
        # pylint:disable-msg=C0111,R0201
        idhost = get_parent_id("hosts")
        pds = get_pds(idpds, idhost)
        result = {
                "id": pds.idperfdatasource,
                "href": tg.url("/api/v%s/hosts/%s/perfdatasources/%s"
                       % (self.apiver, pds.host.idhost, pds.idperfdatasource)),
                "host": {
                    "id": pds.host.idhost,
                    "name": pds.host.name,
                    "href": tg.url("/api/v%s/hosts/%s" % (self.apiver, pds.host.idhost)),
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
                "href": tg.url("/api/v%s/graphs/%s" % (self.apiver, graph.idgraph)),
                "name": graph.name,
                })
        result["graphs"] = graphs
        return dict(pds=result)
