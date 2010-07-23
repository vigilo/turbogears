# -*- coding: utf-8 -*-

"""
API REST d'accès aux ressources de Vigilo

Une des contraintes est de permettre une sortie XML et une sortie JSON
quasi-équivalentes. Ça oblige à pas mal de répétitions, alors qu'on pourrait
mieux utiliser le langage de templates.
"""

import tg
from tg import expose, request, validate
from tg.decorators import with_trailing_slash

from vigilo.turbogears.controllers import BaseController

from vigilo.turbogears.controllers.api.hosts import HostsController
from vigilo.turbogears.controllers.api.services import ServicesController
from vigilo.turbogears.controllers.api.groups import GroupsController
from vigilo.turbogears.controllers.api.maps import MapsController
from vigilo.turbogears.controllers.api.graphs import GraphsController


class ApiRootController(BaseController):
    """Racine de l'API"""

    hosts = HostsController()
    lls = ServicesController("lls")
    hls = ServicesController("hls")
    supitemgroups = GroupsController("supitem")
    maps = MapsController()
    mapgroups = GroupsController("map")
    graphs = GraphsController()
    graphgroups = GroupsController("graph")


    @with_trailing_slash
    @expose("api/root.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def index(self):
        result = {}
        resources = ["hosts", "lls", "hls", "supitemgroups",
                     "maps", "mapgroups", "graphs", "graphgroups"]
        for resource in resources:
            result[resource] = "/api/%s" % resource
        return {"api": result}

