# -*- coding: utf-8 -*-
"""
API d'interrogation des hôtes
"""

import tg
from tg import expose, request, validate
from tg.controllers import RestController
from tg.decorators import with_trailing_slash
from tg.exceptions import HTTPNotFound

from vigilo.models import tables
from vigilo.models.session import DBSession

from vigilo.turbogears.controllers.api import get_host
from vigilo.turbogears.controllers.api.services import ServicesController
from vigilo.turbogears.controllers.api.graphs import GraphsController
from vigilo.turbogears.controllers.api.perfdatasources import PerfDataSourcesController


class HostsController(RestController):

    lls = ServicesController("lls")
    graphs = GraphsController()
    perfdatasources = PerfDataSourcesController()


    @with_trailing_slash
    @expose("api/hosts-all.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        hosts = DBSession.query(tables.Host).all()
        result = []
        for host in hosts:
            result.append({
                    "id": host.idhost,
                    "href": tg.url("/api/hosts/%s" % host.idhost),
                    "name": host.name,
                    })
        return dict(hosts=result)


    @expose("api/hosts-one.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_one(self, idhost):
        host = get_host(idhost)
        baseurl = tg.url("/api/hosts/%s" % host.idhost)
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
                "name": group.name,
                "href": tg.url("/api/supitemgroups/%s" % group.idgroup),
                })
        result["groups"] = groups
        return dict(host=result)

