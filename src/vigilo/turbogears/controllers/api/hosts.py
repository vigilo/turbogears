# -*- coding: utf-8 -*-
"""
API d'interrogation des hôtes
"""

import tg
from tg import expose, validate
from tg.controllers import RestController
from tg.decorators import with_trailing_slash
from tg.exceptions import HTTPNotFound
from sqlalchemy.sql.expression import or_
from repoze.what.predicates import in_group

from vigilo.models import tables
from vigilo.models.session import DBSession
from vigilo.turbogears.helpers import get_current_user
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
        user = get_current_user()
        if not user:
            raise HTTPForbidden("You must be logged in")
        hostgroup = tables.secondary_tables.SUPITEM_GROUP_TABLE.alias()
        servicegroup = tables.secondary_tables.SUPITEM_GROUP_TABLE.alias()
        hosts = DBSession.query(
                tables.Host.idhost, tables.Host.name
            ).distinct(
            ).outerjoin(
                (hostgroup, hostgroup.c.idsupitem == tables.Host.idhost),
                (tables.LowLevelService,
                    tables.LowLevelService.idhost == tables.Host.idhost),
                (servicegroup,
                    servicegroup.c.idsupitem == tables.LowLevelService.idservice),
            )
        # ACLs
        is_manager = in_group('managers').is_met(tg.request.environ)
        if not is_manager:
            user_groups = [ug[0] for ug in user.supitemgroups() if ug[1]]
            hosts = hosts.filter(or_(
                hostgroup.c.idgroup.in_(user_groups),
                servicegroup.c.idgroup.in_(user_groups),
            ))

        hosts = hosts.all()
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

