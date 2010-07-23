# -*- coding: utf-8 -*-
"""
API d'interrogation des hôtes
"""

import os

import tg
from tg import expose, request, validate
from tg.decorators import with_trailing_slash
from tg.controllers import RestController

from vigilo.models import tables
from vigilo.models.session import DBSession


class GroupsController(RestController):


    def __init__(self, group_type):
        super(GroupsController, self).__init__()
        self.type = group_type
        if self.type == "map":
            self.model_class = tables.MapGroup
        elif self.type == "graph":
            self.model_class = tables.GraphGroup
        elif self.type == "supitem":
            self.model_class = tables.SupItemGroup
        else:
            LOGGER.warning("Unknown group type: %s", self.type)


    @with_trailing_slash
    @expose("api/groups-all.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        """
        On retourne la hiérarchie étage par étage
        """
        top_groups = self.model_class.get_top_groups()
        groups = []
        for group in top_groups:
            groups.append({
                "id": group.idgroup,
                "name": group.name,
                "href": tg.url("/api/%sgroups/%s" % (self.type, group.idgroup)),
                })
        return dict(groups=groups, type=self.type)


    @expose("api/groups-one.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_one(self, idgroup):
        group = DBSession.query(self.model_class).get(idgroup)
        result = {"id": group.idgroup,
                  "name": group.name,
                  "href": tg.url("/api/%sgroups/%s" % (self.type, group.idgroup)),
                  }
        children = []
        for subgroup in group.get_children():
            children.append({
                "id": subgroup.idgroup,
                "name": subgroup.name,
                "href": tg.url("/api/%sgroups/%s" % (self.type, subgroup.idgroup)),
                })
        result["children"] = children
        if self.type == "map":
            maps = []
            for m in group.maps:
                maps.append({
                    "id": m.idmap,
                    "title": m.title,
                    "href": tg.url("/api/maps/%s" % m.idmap),
                    })
            result["maps"] = maps
        if self.type == "graph":
            graphs = []
            for graph in group.graphs:
                graphs.append({
                    "id": graph.idgraph,
                    "href": tg.url("/api/graphs/%s" % graph.idgraph),
                    "name": graph.name,
                    })
            result["graphs"] = graphs
        if self.type == "supitem":
            supitems = {"hosts": [], "lls": [], "hls": []}
            for host in group.hosts:
                supitems["hosts"].append({
                        "id": host.idhost,
                        "href": tg.url("/api/hosts/%s" % host.idhost),
                        "name": host.name,
                        })
            for lls in group.lls:
                supitems["lls"].append({
                    "id": lls.idservice,
                    "href": tg.url("/api/lls/%s" % lls.idservice),
                    "name": lls.servicename,
                    })
            for hls in group.hls:
                supitems["hls"].append({
                    "id": hls.idservice,
                    "href": tg.url("/api/hls/%s" % hls.idservice),
                    "name": hls.servicename,
                    })
            result.update(supitems)
        return dict(group=result, type=self.type)

