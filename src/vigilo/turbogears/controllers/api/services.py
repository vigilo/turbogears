# -*- coding: utf-8 -*-
"""
API d'interrogation des hôtes
"""

import logging

import pylons

import tg
from tg import expose, request, validate
from tg.decorators import with_trailing_slash
from tg.controllers import RestController
from tg.exceptions import HTTPNotFound

from vigilo.models import tables
from vigilo.models.session import DBSession

from vigilo.turbogears.controllers.api import get_host, get_service, get_parent_id


LOGGER = logging.getLogger(__name__)


class ServicesController(RestController):

    def __init__(self, service_type):
        super(ServicesController, self).__init__()
        self.type = service_type
        if self.type == "lls":
            self.model_class = tables.LowLevelService
        elif self.type == "hls":
            self.model_class = tables.HighLevelService
        else:
            LOGGER.warning("Unknown service type: %s", self.type)

    #def __before__(self, *args, **kw):
    #    if request.url.endswith("/"):
    #        idhost = request.url.split('/')[-3]
    #    else:
    #        idhost = request.url.split('/')[-2]
    #    print "="*20, idhost
    #    # pylons.c: le contexte du template
    #    pylons.c.host = DBSession.query(tables.Host).get(idhost)


    @with_trailing_slash
    @expose("api/services-all.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        idhost = get_parent_id("hosts")
        if idhost is not None:
            host = get_host(idhost)
            services = host.services
        else:
            services = DBSession.query(self.model_class).all()
        result = []
        for service in services:
            result.append({
                "id": service.idservice,
                "type": self.type,
                "href": tg.url("/api/%s/%s" % (self.type, service.idservice)),
                "name": service.servicename,
                })
        return dict(services=result)


    @expose("api/services-one.xml",
            content_type="application/vnd.vigilo.api+xml; charset=utf-8")
    @expose("json")
    def get_one(self, idservice):
        idhost = get_parent_id("hosts")
        service = get_service(idservice, self.type, idhost)
        result = {"id": service.idservice,
                  "type": self.type,
                  "name": service.servicename,
                  "href": tg.url("/api/%s/%s" % (self.type, service.idservice))
                  }
        status = {
                "name": service.state.name.statename,
                "message": service.state.message,
                "datetime": service.state.timestamp.isoformat(),
                "order": service.state.name.order,
                }
        result["status"] = status
        result["tags"] = [t.name for t in service.tags]
        groups = []
        for group in service.groups:
            groups.append({
                "id": group.idgroup,
                "name": group.name,
                })
        result["groups"] = groups
        if isinstance(service, tables.LowLevelService):
            result["host"] = {
                    "id": service.host.idhost,
                    "name": service.host.name,
                    "href": tg.url("/api/hosts/%s/" % service.host.idhost)
                    }
        else:
            result["host"] = None
        return dict(service=result)
