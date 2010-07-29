# -*- coding: utf-8 -*-

"""
API REST d'accès aux ressources de Vigilo

Une des contraintes est de permettre une sortie XML et une sortie JSON
quasi-équivalentes. Ça oblige à pas mal de répétitions, alors qu'on
pourrait mieux utiliser le langage de templates.
"""

from tg import expose
from tg.decorators import with_trailing_slash
from pylons.i18n import lazy_ugettext as l_
from repoze.what.predicates import not_anonymous

from vigilo.turbogears.controllers import BaseController

from vigilo.turbogears.controllers.api.hosts import HostsController
from vigilo.turbogears.controllers.api.services import ServicesController
from vigilo.turbogears.controllers.api.groups import GroupsController
from vigilo.turbogears.controllers.api.maps import MapsController
from vigilo.turbogears.controllers.api.graphs import GraphsController


class ApiRootController(BaseController):
    """Racine de l'API"""

    # Messages PyLint qu'on supprime
    # - R0201: method could be a function: c'est le fonctionnement du
    #   Controller TurboGears
    # - C0111: missing docstring: la fonction index est définie dans le
    #   Controller


    # Prédicat pour la restriction de l'accès aux interfaces.
    access_restriction = not_anonymous(msg=l_("You need to be authenticated"))
    #access_restriction = All(
    #    not_anonymous(msg=l_("You need to be authenticated")),
    #    Any(in_group('managers'),
    #        has_permission('vigimap-access'),
    #        msg=l_("You don't have read access to VigiMap"))
    #)

    hosts = HostsController()
    lls = ServicesController("lls")
    hls = ServicesController("hls")
    supitemgroups = GroupsController("supitem")
    maps = MapsController()
    mapgroups = GroupsController("map")
    graphs = GraphsController()
    graphgroups = GroupsController("graph")


    @with_trailing_slash
    @expose("json")
    @expose("api/root.xml", content_type="application/xml; charset=utf-8")
    def index(self):
        # pylint:disable-msg=C0111,R0201
        result = {}
        resources = ["hosts", "lls", "hls", "supitemgroups",
                     "maps", "mapgroups", "graphs", "graphgroups"]
        for resource in resources:
            result[resource] = "/api/%s" % resource
        return {"api": result}

