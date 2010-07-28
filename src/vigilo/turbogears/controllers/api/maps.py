# -*- coding: utf-8 -*-
"""
API d'interrogation des hôtes
"""


import tg
from tg import expose
from tg.decorators import with_trailing_slash
from tg.controllers import RestController
from tg.exceptions import HTTPNotFound, HTTPForbidden

from vigilo.models import tables
from vigilo.models.session import DBSession

from vigilo.turbogears.helpers import get_current_user
from vigilo.turbogears.controllers.api import check_map_access
from vigilo.turbogears.controllers.api.mapnodes import MapNodesController
from vigilo.turbogears.controllers.api.maplinks import MapLinksController


class MapsController(RestController):
    """
    Récupération des L{Map<tables.Map>}s
    """

    # Messages PyLint qu'on supprime
    # - R0201: method could be a function: c'est le fonctionnement du
    #   RestController
    # - C0111: missing docstring: les fonctions get_all et get_one sont
    #   définies dans le RestController

    nodes = MapNodesController()
    links = MapLinksController()


    @with_trailing_slash
    @expose("api/maps-all.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        # pylint:disable-msg=C0111,R0201
        user = get_current_user()
        #user = tables.User.by_user_name(u"editor") # debug
        if not user:
            raise HTTPForbidden("You must be logged in")
        mapgroups = user.mapgroups(only_id=False, only_direct=True)
        result = []
        for mapgroup in mapgroups:
            for m in mapgroup.maps:
                if m.idmap in [mr["id"] for mr in result]:
                    continue # Déjà ajouté
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
        # pylint:disable-msg=C0111,R0201
        m = DBSession.query(tables.Map).get(idmap)
        if m is None:
            raise HTTPNotFound("Can't find map %s" % idmap)
        check_map_access(m)
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
        for link in DBSession.query(tables.MapLink).filter_by(
                                    idmap=idmap).all():
            links.append({
                "id": link.idmaplink,
                "href": "%s/links/%s" % (baseurl, link.idmaplink)
                })
        result["links"] = links
        return dict(map=result)

