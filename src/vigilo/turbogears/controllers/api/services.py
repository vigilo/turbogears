# -*- coding: utf-8 -*-
# Copyright (C) 2006-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
API d'interrogation des hôtes
"""


import logging

import tg
from tg import expose
from tg.decorators import with_trailing_slash
from tg.controllers import RestController
from tg.exceptions import HTTPNotFound

from vigilo.models.tables import Service, LowLevelService, HighLevelService

from vigilo.turbogears.controllers.api import get_host, get_all_services, \
        get_service, get_parent_id


LOGGER = logging.getLogger(__name__)


class ServicesV1(RestController):
    """
    Récupération des sous-classes de L{Service}, c'est à dire
    L{LowLevelService} et L{HighLevelService}. Le choix du type se fait par
    passage d'argument au constructeur de la classe.

    Ce contrôlleur peut être monté soit à la racine soit sous un hôte. Il
    traite alors des services de bas niveau uniquement.

    @ivar type: type de service, passé en argument. Soit C{lls} soit C{hls}
    @type type: C{str}
    @ivar model_class: classe du modèle correspondante au type, c'est à dire
        soit L{LowLevelService} soit L{HighLevelService}.
    @type model_class: sous-classe de L{Service}
    """

    # Messages PyLint qu'on supprime
    # - R0201: method could be a function: c'est le fonctionnement du
    #   RestController
    # - C0111: missing docstring: les fonctions get_all et get_one sont
    #   définies dans le RestController

    apiver = 1


    def __init__(self, service_type):
        """
        @param service_type: type de service, passé en argument. Soit C{lls}
            soit C{hls}
        @type  service_type: C{str}
        """
        super(ServicesV1, self).__init__()
        self.type = service_type
        if self.type == "lls":
            self.model_class = LowLevelService
        elif self.type == "hls":
            self.model_class = HighLevelService
        else:
            LOGGER.warning("Unknown service type: %s", self.type)


    @with_trailing_slash
    @expose("api/services-all.xml",
            content_type="application/xml; charset=utf-8")
    @expose("json")
    def get_all(self):
        # pylint:disable-msg=C0111,R0201
        idhost = get_parent_id("hosts")
        if idhost is not None:
            host = get_host(idhost)
            services = host.services
        else:
            services = get_all_services(self.model_class)
        result = []
        for service in services:
            result.append({
                "id": service.idservice,
                "type": self.type,
                "href": tg.url("/api/v%s/%s/%s"
                            % (self.apiver, self.type, service.idservice)),
                "name": service.servicename,
                })
        return dict(services=result)


    @expose("api/services-one.xml",
            content_type="application/xml; charset=utf-8")
    @expose("json")
    def get_one(self, idservice):
        # pylint:disable-msg=C0111,R0201
        idhost = get_parent_id("hosts")
        service = get_service(idservice, self.type, idhost)
        if not service:
            raise HTTPNotFound("Can't find service %s" % idservice)
        result = {"id": service.idservice,
                  "type": self.type,
                  "name": service.servicename,
                  "href": tg.url("/api/v%s/%s/%s"
                            % (self.apiver, self.type, service.idservice))
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
        if isinstance(service, LowLevelService):
            result["host"] = {
                    "id": service.host.idhost,
                    "name": service.host.name,
                    "href": tg.url("/api/v%s/hosts/%s"
                                % (self.apiver, service.host.idhost)),
                    }
        else:
            result["host"] = None
        return dict(service=result)
