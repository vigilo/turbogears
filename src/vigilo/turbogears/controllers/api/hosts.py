# -*- coding: utf-8 -*-
# Copyright (C) 2006-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
API d'interrogation des hôtes
"""


import tg
from tg import expose
from tg.controllers import RestController
from tg.decorators import with_trailing_slash

#from vigilo.models import tables
#from vigilo.models.session import DBSession
from vigilo.turbogears.controllers.api import get_all_hosts, get_host
from vigilo.turbogears.controllers.api.services import ServicesV1
from vigilo.turbogears.controllers.api.graphs import GraphsV1
from vigilo.turbogears.controllers.api.perfdatasources import PerfDataSourcesV1


class HostsV1(RestController):
    """
    Contrôleur permettant de récupérer des hôtes (C{tables.Host}).
    """

    # Messages PyLint qu'on supprime
    # - R0201: method could be a function: c'est le fonctionnement du
    #   RestController
    # - C0111: missing docstring: les fonctions get_all et get_one sont
    #   définies dans le RestController

    apiver = 1

    lls = ServicesV1("lls")
    graphs = GraphsV1()
    perfdatasources = PerfDataSourcesV1()


    @with_trailing_slash
    @expose("api/hosts-all.xml", content_type="application/xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        # pylint:disable-msg=C0111,R0201
        hosts = get_all_hosts()
        result = []
        for host in hosts:
            result.append({
                    "id": host.idhost,
                    "href": tg.url("/api/v%s/hosts/%s" % (self.apiver, host.idhost)),
                    "name": host.name,
                    })
        return dict(hosts=result)


    @expose("api/hosts-one.xml", content_type="application/xml; charset=utf-8")
    @expose("json")
    def get_one(self, idhost):
        # pylint:disable-msg=C0111,R0201
        host = get_host(idhost)
        baseurl = tg.url("/api/v%s/hosts/%s" % (self.apiver, host.idhost))
        result = {"id": host.idhost,
                  "name": host.name,
                  "href": baseurl,
                  "description": host.description,
                  "address": host.address,
                  "status": {
                      "name": host.state.name.statename,
                      "message": host.state.message,
                      "datetime": host.state.timestamp.isoformat(),
                      "order": host.state.name.order,
                      },
                  "tags": [t.name for t in host.tags],
                  }
        result["lls"] = baseurl+"/lls/"
        result["perfdatasources"] = baseurl+"/perfdatasources/"
        result["graphs"] = baseurl+"/graphs/"
        groups = []
        for group in host.groups:
            groups.append({
                "id": group.idgroup,
                "name": group.path,
                "href": tg.url("/api/v%s/supitemgroups/%s"
                               % (self.apiver, group.idgroup)),
                })
        result["groups"] = groups
        return dict(host=result)

