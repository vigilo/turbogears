# -*- coding: utf-8 -*-
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
API REST d'accès aux ressources de Vigilo

Une des contraintes est de permettre une sortie XML et une sortie JSON
quasi-équivalentes. Ça oblige à pas mal de répétitions, alors qu'on
pourrait mieux utiliser le langage de templates.
"""

import tg
from tg import expose
from tg.decorators import with_trailing_slash
from tg.i18n import lazy_ugettext as l_
from tg.predicates import not_anonymous

from vigilo.turbogears.controllers import BaseController

from vigilo.turbogears.controllers.api.hosts import HostsV1
from vigilo.turbogears.controllers.api.services import ServicesV1
from vigilo.turbogears.controllers.api.groups import GroupsV1
from vigilo.turbogears.controllers.api.maps import MapsV1
from vigilo.turbogears.controllers.api.graphs import GraphsV1


class ApiV1Controller(BaseController):

    hosts = HostsV1()
    lls = ServicesV1("lls")
    hls = ServicesV1("hls")
    supitemgroups = GroupsV1("supitem")
    maps = MapsV1()
    mapgroups = GroupsV1("map")
    graphs = GraphsV1()
    graphgroups = GroupsV1("graph")

    @with_trailing_slash
    @expose("json")
    @expose("api/v1.xml", content_type="application/xml; charset=utf-8")
    def index(self):
        # pylint:disable-msg=C0111,R0201
        result = {}
        resources = ["hosts", "lls", "hls", "supitemgroups",
                     "maps", "mapgroups", "graphs", "graphgroups"]
        for resource in resources:
            result[resource] = tg.url("/api/v1/%s" % resource)
        return {"api": result}


class ApiRootController(BaseController):
    """Racine de l'API"""

    # Messages PyLint qu'on supprime
    # - R0201: method could be a function: c'est le fonctionnement du
    #   Controller TurboGears
    # - C0111: missing docstring: la fonction index est définie dans le
    #   Controller


    # Prédicat pour la restriction de l'accès aux interfaces.
    allow_only = not_anonymous(msg=l_("You need to be authenticated"))
    #access_restriction = All(
    #    not_anonymous(msg=l_("You need to be authenticated")),
    #    Any(in_group('managers'),
    #        has_permission('vigimap-access'),
    #        msg=l_("You don't have read access to VigiMap"))
    #)

    v1 = ApiV1Controller()

    @with_trailing_slash
    @expose("json")
    @expose("api/root.xml", content_type="application/xml; charset=utf-8")
    def index(self):
        # pylint:disable-msg=C0111,R0201
        result = [{"version": 1, "href": tg.url("/api/v1")}, ]
        return {"apis": result}
