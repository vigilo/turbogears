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

from vigilo.turbogears.controllers.api import get_parent_id


class MapLinksController(RestController):


    @with_trailing_slash
    @expose("api/maplinks-all.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        idmap = get_parent_id("maps")
        if idmap is not None:
            map = DBSession.query(tables.Map).get(idmap)
        else:
            raise HTTPNotFound("The URL seems invalid (no map found)")
        links = DBSession.query(tables.MapLink).filter_by(idmap=idmap).all()
        result = []
        for link in links:
            result.append({
                "id": link.idmaplink,
                "href": tg.url("/api/maps/%s/links/%s" % (idmap, link.idmaplink)),
                })
        return dict(maplinks=result)


    @expose("api/maplinks-one.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_one(self, idmaplink):
        link = DBSession.query(tables.MapLink).get(idmaplink)
        result = {"id": link.idmaplink,
                  "from": {
                      "id": link.idfrom_node,
                      "href": tg.url("/api/mapnodes/%s" % link.idfrom_node),
                      },
                  "to": {
                      "id": link.idto_node,
                      "href": tg.url("/api/mapnodes/%s" % link.idto_node),
                      },
                  }
        # Spécifique MapServiceLink
        if isinstance(link, tables.MapServiceLink):
            if link.idgraph:
                result["graph"] = {
                        "id": link.idgraph,
                        "href": tg.url("/api/graphs/%s" % link.idgraph)
                        }
            datasources = {}
            if link.idds_from_to_to:
                datasources["out"] = {
                        "id": link.idds_from_to_to,
                        "href": tg.url("/api/perfdatasources/%s" % link.idds_from_to_to),
                        }
            if link.idds_to_to_from:
                datasources["in"] = {
                        "id": link.idds_to_to_from,
                        "href": tg.url("/api/perfdatasources/%s" % link.idds_to_to_from),
                        }
            result["perfdatasources"] = datasources
            result["reference"] = {"id": link.idref}
            if isinstance(link, tables.MapLlsLink):
                result["reference"]["href"] = tg.url("/api/lls/%s" % link.idref)
            elif isinstance(link, tables.MapHlsLink):
                result["reference"]["href"] = tg.url("/api/hls/%s" % link.idref)
        # Spécifique MapSegment
        elif isinstance(link, tables.MapSegment):
            result["color"] = link.color,
            result["thickness"] = link.thickness
        return dict(link=result)
