# -*- coding: utf-8 -*-
"""
Module permettant de mettre en commun le contrôleur d'auto-complétion
entre les différentes applications de Vigilo.
"""
from tg import expose, request
from sqlalchemy.sql.expression import or_

from vigilo.models.tables import Host, HostGroup, ServiceGroup, \
                                    LowLevelService, User
from vigilo.models.session import DBSession
from vigilo.models.functions import sql_escape_like
from vigilo.models.tables.secondary_tables import HOST_GROUP_TABLE, \
                                                    SERVICE_GROUP_TABLE

# pylint: disable-msg=R0201,W0232
# - R0201: méthodes pouvant être écrites comme fonctions (imposé par TG2)
# - W0232: absence de __init__ dans la classe (imposé par TG2)

def make_autocomplete_controller(base_controller):
    """
    Renvoie une instance du contrôleur d'auto-complétion adaptée
    à l'application qui en fait la demande.

    @param base_controller: Contrôleur basic de l'application.
    @type base_controller: C{BaseController}
    @return: Une instance du contrôleur d'auto-complétion.
    @rtype: L{AutoCompleteControllerHelper}
    """

    class AutoCompleteControllerHelper(base_controller):
        """Contrôleur d'auto-complétion."""

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
            @return: Un dictionnaire dont la clé 'results' contient la liste
                des noms d'hôtes correspondant au motif donné en entrée
                et auxquels l'utilisateur a accès.
            @rtype: C{dict}
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
                    (HOST_GROUP_TABLE, HOST_GROUP_TABLE.c.idhost == \
                        Host.idhost),
                    (LowLevelService, LowLevelService.idhost == Host.idhost),
                    (SERVICE_GROUP_TABLE, SERVICE_GROUP_TABLE.c.idservice == \
                        LowLevelService.idservice),
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
            
            @param host: Nom d'hôte (optionnel) sur lequel s'applique
                l'autocomplétion.
            @type host: C{unicode}
            @param service: Motif qui doit apparaître dans le nom de service.
            @type service: C{unicode}
            @note: Les caractères '?' et '*' peuvent être utilisés dans
                le paramètre L{service} pour remplacer un caractère quelconque
                ou une chaîne de caractères, respectivement.
                Ex: 'ho?t*' permet de récupérer 'host', 'honte' et 'hostile',
                mais pas 'hote' ou 'hopital'.
            @return: Un dictionnaire dont la clé 'results' contient la liste
                des noms de services configurés sur L{host} (ou sur n'importe
                quel hôte si L{host} vaut None), correspondant au motif donné
                et auxquels l'utilisateur a accès.
            @rtype: C{dict}
            """
            service = sql_escape_like(service)
            username = request.environ.get('repoze.who.identity'
                        ).get('repoze.who.userid')

            user = User.by_user_name(username)
            if not user:
                return dict(results=[])

            user_groups = user.groups
            services = DBSession.query(
                    LowLevelService.servicename
                ).distinct(
                ).outerjoin(
                    (Host, Host.idhost == LowLevelService.idhost),
                    (HOST_GROUP_TABLE, HOST_GROUP_TABLE.c.idhost == \
                        Host.idhost),
                    (SERVICE_GROUP_TABLE, SERVICE_GROUP_TABLE.c.idservice == \
                        LowLevelService.idservice),
                ).filter(LowLevelService.servicename.ilike('%' + service + '%')
                ).filter(or_(
                    HOST_GROUP_TABLE.c.idgroup.in_(user_groups),
                    SERVICE_GROUP_TABLE.c.idgroup.in_(user_groups),
                ))

            if host:
                services = services.filter(Host.name == host)
            services = services.all()

            return dict(results=[s[0] for s in services])

        @expose('json')
        def hostgroup(self, hostgroup):
            """
            Auto-compléteur pour les noms des groupes d'hôtes.

            @param hostgroup: Motif qui doit apparaître dans le nom
                du groupe d'hôtes.
            @type hostgroup: C{unicode}
            @return: Un dictionnaire dont la clé 'results' contient la liste
                des noms de groupes d'hôtes correspondant au motif donné
                et auxquels l'utilisateur a accès.
            @rtype: C{dict}
            """
            hostgroup = sql_escape_like(hostgroup)
            username = request.environ.get('repoze.who.identity'
                        ).get('repoze.who.userid')

            user = User.by_user_name(username)
            if not user:
                return dict(results=[])

            user_groups = user.groups
            hostgroups = DBSession.query(
                    HostGroup.name
                ).distinct(
                ).filter(HostGroup.name.ilike('%' + hostgroup + '%')
                ).filter(HostGroup.idgroup.in_(user_groups)
                ).all()
            return dict(results=[h[0] for h in hostgroups])

        @expose('json')
        def servicegroup(self, servicegroup):
            """
            Auto-compléteur pour les noms des groupes de services.

            @param servicegroup: Motif qui doit apparaître dans le nom
                du groupe de service.
            @type servicegroup: C{unicode}
            @return: Un dictionnaire dont la clé 'results' contient la liste
                des noms de groupes de services correspondant au motif donné
                et auxquels l'utilisateur a accès.
            @rtype: C{dict}
            """
            servicegroup = sql_escape_like(servicegroup)
            username = request.environ.get('repoze.who.identity'
                        ).get('repoze.who.userid')

            user = User.by_user_name(username)
            if not user:
                return dict(results=[])

            user_groups = user.groups
            servicegroups = DBSession.query(
                    ServiceGroup.name
                ).distinct(
                ).filter(ServiceGroup.name.ilike('%' + servicegroup + '%')
                ).filter(ServiceGroup.idgroup.in_(user_groups)
                ).all()
            return dict(results=[s[0] for s in servicegroups])

    return AutoCompleteControllerHelper()

