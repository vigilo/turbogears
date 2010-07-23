# -*- coding: utf-8 -*-
"""
API d'interrogation des hôtes
"""

import tg
from tg import expose, request, validate
from tg.decorators import with_trailing_slash
from tg.controllers import RestController

from vigilo.models import tables
from vigilo.models.session import DBSession

from vigilo.turbogears.controllers.api.mapnodes import MapNodesController
from vigilo.turbogears.controllers.api.maplinks import MapLinksController
from vigilo.turbogears.controllers.api.groups import GroupsController


class MapsController(RestController):

    nodes = MapNodesController()
    links = MapLinksController()
    groups = GroupsController("map")


    @with_trailing_slash
    @expose("api/maps-all.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        maps = DBSession.query(tables.Map).all()
        result = []
        for m in maps:
            result.append({
                "id": m.idmap,
                "href": tg.url("/api/maps/%s" % m.idmap),
                "title": m.title,
                })
        return dict(maps=result)


    @expose("api/maps-one.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_one(self, idmap):
        m = DBSession.query(tables.Map).get(idmap)
        result = {"id": m.idmap,
                  "title": m.title,
                  "mtime": m.mtime.isoformat(),
                  "generated": m.generated,
                  "background": {
                      "color": m.background_color,
                      "image": m.background_image,
                      "position": m.background_position,
                      "repeat": m.background_repeat,
                      },
                  }
        baseurl = tg.url("/api/maps/%s" % m.idmap)
        # groups
        result["groups_href"] = baseurl+"/groups/"
        groups = []
        for group in m.groups:
            groups.append({
                "id": group.idgroup,
                "name": group.name,
                "href": tg.url("/api/mapgroups/%s" % group.idgroup),
                })
        result["groups"] = groups
        # nodes
        result["nodes_href"] = baseurl+"/nodes/"
        nodes = []
        for node in m.nodes:
            nodes.append({
                "id": node.idmapnode,
                "href": "%s/nodes/%s" % (baseurl, node.idmapnode)
                })
        result["nodes"] = nodes
        # links
        result["links_href"] = baseurl+"/links/"
        links = []
        for link in DBSession.query(tables.MapLink).filter_by(idmap=idmap).all():
            links.append({
                "id": link.idmaplink,
                "href": "%s/links/%s" % (baseurl, link.idmaplink)
                })
        result["links"] = links
        return dict(map=result)

