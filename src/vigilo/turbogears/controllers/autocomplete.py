# -*- coding: utf-8 -*-
from tg import expose, request
from sqlalchemy.sql.expression import or_

from vigilo.models import Host, ServiceLowLevel, User
from vigilo.models.session import DBSession
from vigilo.models.functions import sql_escape_like
from vigilo.models.secondary_tables import HOST_GROUP_TABLE, \
                                            SERVICE_GROUP_TABLE

def AutoCompleteController(base_controller):
    class AutoCompleteControllerHelper(base_controller):
        @expose('json')
        def host(self, host):
            """
            Auto-compléteur pour les noms d'hôtes.
            
            @param host: Motif qui doit apparaître dans le nom de l'hôte.
            @type host: C{unicode}
            @note: Les caractères '?' et '*' peuvent être utilisés dans
                le paramètre L{host} pour remplacer un caractère quelconque
                ou une chaîne de caractères, respectivement.
                Ex: 'ho?t*' permet de récupérer 'host', 'honte' et 'hostile',
                mais pas 'hote' ou 'hopital'.
            @return: Liste des noms d'hôtes configurés correspondant au
                motif donné en entrée.
            @rtype: C{list} of C{unicode}
            """
            host = sql_escape_like(host)

            username = request.environ.get('repoze.who.identity'
                        ).get('repoze.who.userid')
            user = User.by_user_name(username)
            if not user:
                return dict(results=[])

            user_groups = user.groups
            hostnames = DBSession.query(
                    Host.name
                ).distinct(
                ).outerjoin(
                    (HOST_GROUP_TABLE, HOST_GROUP_TABLE.c.idhost == Host.idhost),
                    (ServiceLowLevel, ServiceLowLevel.idhost == Host.idhost),
                    (SERVICE_GROUP_TABLE, SERVICE_GROUP_TABLE.c.idservice == \
                        ServiceLowLevel.idservice),
                ).filter(Host.name.ilike('%' + host + '%')
                ).filter(or_(
                    HOST_GROUP_TABLE.c.idgroup.in_(user_groups),
                    SERVICE_GROUP_TABLE.c.idgroup.in_(user_groups),
                )).all()
            return dict(results=[h[0] for h in hostnames])

        @expose('json')
        def service(self, service, host=None):
            """
            Auto-compléteur pour les noms des services d'un hôte.
            
            @param host: Nom d'hôte sur lequel s'applique l'autocomplétion.
            @type host: C{unicode}
            @param service: Motif qui doit apparaître dans le nom de service.
            @type service: C{unicode}
            @note: Les caractères '?' et '*' peuvent être utilisés dans
                le paramètre L{service} pour remplacer un caractère quelconque
                ou une chaîne de caractères, respectivement.
                Ex: 'ho?t*' permet de récupérer 'host', 'honte' et 'hostile',
                mais pas 'hote' ou 'hopital'.
            @return: Liste des noms de services configurés sur cet L{host}
                et correspondant au motif donné en entrée.
            @rtype: C{list} of C{unicode}
            """
            service = sql_escape_like(service)
            username = request.environ.get('repoze.who.identity'
                        ).get('repoze.who.userid')

            user = User.by_user_name(username)
            if not user:
                return dict(results=[])

            user_groups = user.groups
            services = DBSession.query(
                    ServiceLowLevel.servicename
                ).distinct(
                ).outerjoin(
                    (Host, Host.idhost == ServiceLowLevel.idhost),
                    (HOST_GROUP_TABLE, HOST_GROUP_TABLE.c.idhost == Host.idhost),
                    (SERVICE_GROUP_TABLE, SERVICE_GROUP_TABLE.c.idservice == \
                        ServiceLowLevel.idservice),
                ).filter(ServiceLowLevel.servicename.ilike('%' + service + '%')
                ).filter(or_(
                    HOST_GROUP_TABLE.c.idgroup.in_(user_groups),
                    SERVICE_GROUP_TABLE.c.idgroup.in_(user_groups),
                ))

            if host:
                services = services.filter(Host.name == host)
            services = services.all()

            return dict(results=[s[0] for s in services])

        @expose('json')
        def hostgroup(self, value):
    #        username = request.environ.get('repoze.who.identity'
    #                    ).get('repoze.who.userid')
            value = sql_escape_like(value)
            hostgroups = DBSession.query(
                            HostGroup.name.distinct()).filter(
                            HostGroup.name.ilike('%' + value + '%')).all()
            return dict(results=[h[0] for h in hostgroups])

        @expose('json')
        def servicegroup(self, value):
    #        username = request.environ.get('repoze.who.identity'
    #                    ).get('repoze.who.userid')
            value = sql_escape_like(value)
            servicegroups = DBSession.query(
                            ServiceGroup.name.distinct()).filter(
                            ServiceGroup.name.ilike('%' + value + '%')).all()
            return dict(results=[s[0] for s in servicegroups])

    return AutoCompleteControllerHelper()

