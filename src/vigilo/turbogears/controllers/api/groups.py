# -*- coding: utf-8 -*-
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
API d'interrogation des hôtes
"""

import logging

import tg
from tg import expose
from tg.decorators import with_trailing_slash
from tg.controllers import RestController
from tg.exceptions import HTTPNotFound, HTTPForbidden

from vigilo.models.tables import MapGroup, GraphGroup, SupItemGroup
from vigilo.models.tables.group import Group
from vigilo.models.session import DBSession

from vigilo.turbogears.helpers import get_current_user


LOGGER = logging.getLogger(__name__)


class GroupsV1(RestController):
    """
    Contrôleur permettant de récupérer des sous-classes de L{Group},
    c'est à dire L{MapGroup}, L{GraphGroup}, ou L{SupItemGroup}.
    Le choix du type se fait par passage d'argument au constructeur de la
    classe.

    Ce contrôlleur est monté à la racine, sous plusieurs identifiants
    correspondants au type de groups désiré.

    @ivar type: type de groupe, passé en argument. Soit C{map} soit C{graph}
        soit C{supitem}
    @type type: C{str}
    @ivar model_class: classe du modèle correspondante au type, c'est à dire
        soit L{MapGroup} soit L{GraphGroup} soit L{SupItemGroup}
    @type model_class: sous-classe de L{Group}
    """

    apiver = 1


    def __init__(self, group_type):
        """
        @param group_type: type de groupe, passé en argument. Soit C{map} soit
            C{graph} soit C{supitem}
        @type  group_type: C{str}
        """
        super(GroupsV1, self).__init__()
        self.type = group_type
        if self.type == "map":
            self.model_class = MapGroup
        elif self.type == "graph":
            self.model_class = GraphGroup
        elif self.type == "supitem":
            self.model_class = SupItemGroup
        else:
            LOGGER.warning("Unknown group type: %s", self.type)

    def _get_allowed_groups(self):
        """
        @return: liste des ID des groupes autorisés pour l'utilisateur courant
        @rtype:  liste de C{int}
        """
        user = get_current_user()
        #user = tables.User.by_user_name(u"editor") # debug
        if not user:
            raise HTTPForbidden("You must be logged in")
        allowed_groups = None
        if self.type == "map":
            allowed_groups = user.mapgroups(only_id=True)
        elif self.type == "supitem":
            allowed_groups = [ g[0] for g in user.supitemgroups() ]
        return allowed_groups

    @with_trailing_slash
    @expose("api/groups-all.xml", content_type="application/xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        """
        On retourne la hiérarchie étage par étage
        """
        top_groups = self.model_class.get_top_groups()
        allowed_groups = self._get_allowed_groups()
        groups = []
        for group in top_groups:
            if allowed_groups is not None and \
                    group.idgroup not in allowed_groups:
                continue
            groups.append({
                "id": group.idgroup,
                "name": group.name,
                "href": tg.url("/api/v%s/%sgroups/%s"
                               % (self.apiver, self.type, group.idgroup)),
                })
        return dict(groups=groups, type=self.type)


    @expose("api/groups-one.xml", content_type="application/xml; charset=utf-8")
    @expose("json")
    def get_one(self, idgroup):
        # Suppression du message "missing docstring", c'est une méthode
        # standard du contrôlleur REST
        # pylint:disable-msg=C0111
        group = DBSession.query(self.model_class).get(idgroup)
        if not group:
            raise HTTPNotFound("Can't find group %s" % idgroup)
        allowed_groups = self._get_allowed_groups()
        if allowed_groups is not None and int(idgroup) not in allowed_groups:
            raise HTTPForbidden("Access denied to group %s" % idgroup)
        baseurl = tg.url("/api/v%s" % self.apiver)
        result = {"id": group.idgroup,
                  "name": group.name,
                  "href": baseurl + "/%sgroups/%s" %
                                    (self.type, group.idgroup),
                  }
        children = []
        for subgroup in group.get_children():
            if allowed_groups is not None and \
                    subgroup.idgroup not in allowed_groups:
                continue
            children.append({
                "id": subgroup.idgroup,
                "name": subgroup.name,
                "href": baseurl + "/%sgroups/%s" %
                                  (self.type, subgroup.idgroup),
                })
        result["children"] = children
        if self.type == "map":
            maps = []
            for m in group.maps:
                maps.append({
                    "id": m.idmap,
                    "title": m.title,
                    "href": baseurl + "/maps/%s" % m.idmap,
                    })
            result["maps"] = maps
        if self.type == "graph":
            graphs = []
            for graph in group.graphs:
                graphs.append({
                    "id": graph.idgraph,
                    "href": baseurl + "/graphs/%s" % graph.idgraph,
                    "name": graph.name,
                    })
            result["graphs"] = graphs
        if self.type == "supitem":
            supitems = {"hosts": [], "lls": [], "hls": []}
            for host in group.hosts:
                supitems["hosts"].append({
                        "id": host.idhost,
                        "href": baseurl + "/hosts/%s" % host.idhost,
                        "name": host.name,
                        })
            for lls in group.lls:
                supitems["lls"].append({
                    "id": lls.idservice,
                    "href": baseurl + "/lls/%s" % lls.idservice,
                    "name": lls.servicename,
                    })
            for hls in group.hls:
                supitems["hls"].append({
                    "id": hls.idservice,
                    "href": baseurl + "/hls/%s" % hls.idservice,
                    "name": hls.servicename,
                    })
            result.update(supitems)
        return dict(group=result, type=self.type)

