# -*- coding: utf-8 -*-
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Module permettant de mettre en commun le contrôleur d'auto-complétion
entre les différentes applications de Vigilo.
"""
from tg import expose, request, validate
from sqlalchemy.sql.expression import or_
from repoze.what.predicates import in_group

from vigilo.models.tables import Host, SupItemGroup, PerfDataSource, Graph, \
                                    LowLevelService, HighLevelService
from vigilo.models.session import DBSession
from vigilo.models.functions import sql_escape_like
from vigilo.models.tables.secondary_tables import SUPITEM_GROUP_TABLE, \
                                            GRAPH_PERFDATASOURCE_TABLE

from vigilo.turbogears.helpers import get_current_user
from vigilo.turbogears.controllers import BaseController
from tw.forms import validators
from formencode import schema

# pylint: disable-msg=R0201,W0232
# - R0201: méthodes pouvant être écrites comme fonctions (imposé par TG2)
# - W0232: absence de __init__ dans la classe (imposé par TG2)

class AutoCompleteController(BaseController):
    """Contrôleur d'auto-complétion."""

    def __init__(self, allow_only=None):
        super(AutoCompleteController, self).__init__()
        if allow_only:
            self.allow_only = allow_only

    class HostSchema(schema.Schema):
        """
        Schéma de validation de la méthode default.
        """
        host = validators.UnicodeString()
        partial = validators.StringBool(if_missing=False)
        noCache = validators.UnicodeString(if_missing=None)

    @validate(validators=HostSchema())
    @expose('json')
    def host(self, host, partial, noCache):
        """
        Auto-compléteur pour les noms d'hôtes.

        @param host: Motif qui doit apparaître dans le nom de l'hôte.
        @type  host: C{unicode}
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
        user = get_current_user()
        if not user:
            return dict(results=[])

        if partial:
            host += '%'

        hostgroup = SUPITEM_GROUP_TABLE.alias()
        servicegroup = SUPITEM_GROUP_TABLE.alias()
        hostnames = DBSession.query(
                Host.name
            ).distinct(
            ).outerjoin(
                (hostgroup, hostgroup.c.idsupitem == Host.idhost),
                (LowLevelService, LowLevelService.idhost == Host.idhost),
                (servicegroup, servicegroup.c.idsupitem == \
                    LowLevelService.idservice),
            ).filter(Host.name.ilike(host))

        is_manager = in_group('managers').is_met(request.environ)
        if not is_manager:
            user_groups = [ug[0] for ug in user.supitemgroups() if ug[1]]
            hostnames = hostnames.filter(or_(
                hostgroup.c.idgroup.in_(user_groups),
                servicegroup.c.idgroup.in_(user_groups),
            ))

        hostnames = hostnames.all()
        return dict(results=[h.name for h in hostnames])

    class ServiceSchema(schema.Schema):
        """
        Schéma de validation de la méthode default.
        """
        service = validators.UnicodeString()
        host = validators.UnicodeString(if_missing=None)
        partial = validators.StringBool(if_missing=False)
        noCache = validators.UnicodeString(if_missing=None)

    @validate(validators=ServiceSchema())
    @expose('json')
    def service(self, service, host, partial, noCache):
        """
        Auto-compléteur pour les noms des services d'un hôte.

        @param host: Nom d'hôte (optionnel) sur lequel s'applique
            l'autocomplétion.
        @type  host: C{unicode}
        @param service: Motif qui doit apparaître dans le nom de service.
        @type  service: C{unicode}
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
        user = get_current_user()
        if not user:
            return dict(results=[])

        if partial:
            service += '%'

        hostgroup = SUPITEM_GROUP_TABLE.alias()
        servicegroup = SUPITEM_GROUP_TABLE.alias()
        services = DBSession.query(
                LowLevelService.servicename
            ).distinct(
            ).outerjoin(
                (Host, Host.idhost == LowLevelService.idhost),
                (hostgroup, hostgroup.c.idsupitem == Host.idhost),
                (servicegroup, servicegroup.c.idsupitem == \
                    LowLevelService.idservice),
            ).filter(LowLevelService.servicename.ilike(service)
            ).order_by(LowLevelService.servicename)

        is_manager = in_group('managers').is_met(request.environ)
        if not is_manager:
            user_groups = [ug[0] for ug in user.supitemgroups() if ug[1]]
            services = services.filter(or_(
                hostgroup.c.idgroup.in_(user_groups),
                servicegroup.c.idgroup.in_(user_groups),
            ))

        if host:
            services = services.filter(Host.name == host)

        services = services.all()
        return dict(results=[s.servicename for s in services])

    class HlsSchema(schema.Schema):
        """
        Schéma de validation de la méthode default.
        """
        service = validators.UnicodeString()
        partial = validators.StringBool(if_missing=False)
        noCache = validators.UnicodeString(if_missing=None)

    @validate(validators=HlsSchema())
    @expose('json')
    def hls(self, service, partial, noCache):
        """
        Auto-compléteur pour les noms des services de haut niveau.

        @param service: Motif qui doit apparaître dans le nom de service.
        @type  service: C{unicode}
        @note: Les caractères '?' et '*' peuvent être utilisés dans
            le paramètre L{service} pour remplacer un caractère quelconque
            ou une chaîne de caractères, respectivement.
            Ex: 'ho?t*' permet de récupérer 'host', 'honte' et 'hostile',
            mais pas 'hote' ou 'hopital'.
        @return: Un dictionnaire dont la clé 'results' contient la liste
            des noms des services de haut niveau correspondant au motif
            donné et auxquels l'utilisateur a accès.
        @rtype: C{dict}
        """
        service = sql_escape_like(service)
        user = get_current_user()
        if not user:
            return dict(results=[])

        if partial:
            service += '%'

        services = DBSession.query(
                HighLevelService.servicename
            ).distinct(
            ).filter(HighLevelService.servicename.ilike(service)
            ).order_by(HighLevelService.servicename)

#        is_manager = in_group('managers').is_met(request.environ)
#        if not is_manager:
#            user_groups = [ug[0] for ug in user.supitemgroups() if ug[1]]
#            services = services.join(
#                    (SUPITEM_GROUP_TABLE, SUPITEM_GROUP_TABLE.c.idsupitem == \
#                                            HighLevelService.idservice),
#                ).filter(SUPITEM_GROUP_TABLE.c.idgroup.in_(user_groups))

        services = services.all()
        return dict(results=[s.servicename for s in services])

    class SupItemGroupSchema(schema.Schema):
        """Schéma de validation de la méthode default."""
        supitemgroup = validators.UnicodeString()
        partial = validators.StringBool(if_missing=False)
        noCache = validators.UnicodeString(if_missing=None)

    @validate(validators=SupItemGroupSchema())
    @expose('json')
    def supitemgroup(self, supitemgroup, partial, noCache):
        """
        Auto-compléteur pour les noms des groupes d'éléments supervisés.

        @param supitemgroup: Motif qui doit apparaître dans le nom
            du groupe d'éléments supervisés.
        @type supitemgroup: C{unicode}
        @return: Un dictionnaire dont la clé 'results' contient la liste
            des noms de groupes d'élements supervisés correspondant
            au motif donné et auxquels l'utilisateur a accès.
        @rtype: C{dict}
        """
        supitemgroup = sql_escape_like(supitemgroup)
        user = get_current_user()
        if not user:
            return dict(results=[])

        if partial:
            supitemgroup += '%'

        supitemgroups = DBSession.query(
                SupItemGroup.name
            ).distinct(
            ).filter(SupItemGroup.name.ilike(supitemgroup))

        is_manager = in_group('managers').is_met(request.environ)
        if not is_manager:
            user_groups = [ug[0] for ug in user.supitemgroups() if ug[1]]
            supitemgroups = supitemgroups.filter(
                SupItemGroup.idgroup.in_(user_groups),
            )

        supitemgroups = supitemgroups.all()
        return dict(results=[s.name for s in supitemgroups])

    class PerfDataSourceSchema(schema.Schema):
        """Schéma de validation de la méthode default."""
        ds = validators.UnicodeString()
        host = validators.UnicodeString()
        partial = validators.StringBool(if_missing=False)
        noCache = validators.UnicodeString(if_missing=None)

    @validate(validators=PerfDataSourceSchema())
    @expose('json')
    def perfdatasource(self, ds, host, partial, noCache):
        """
        Auto-compléteur pour les noms des indicateurs de performance.

        @param ds: Motif qui doit apparaître dans le nom de l'indicateur.
        @type ds: C{unicode}
        @param host: Nom de l'hôte auquel l'indicateur doit être rattaché.
        @type host: C{unicode}
        @return: Un dictionnaire dont la clé 'results' contient la liste
            des noms des indicateurs de supervision sur L{host} correspondant
            au motif donné et auxquels l'utilisateur a accès.
        @rtype: C{dict}
        """
        ds = sql_escape_like(ds)
        user = get_current_user()
        if not user:
            return dict(results=[])

        if partial:
            ds += '%'

        perfdatasources = DBSession.query(
                PerfDataSource.name
            ).distinct(
            ).join(
                (Host, Host.idhost == PerfDataSource.idhost),
            ).filter(PerfDataSource.name.ilike(ds)
            ).filter(Host.name == host
            ).order_by(PerfDataSource.name)

        is_manager = in_group('managers').is_met(request.environ)
        if not is_manager:
            user_groups = [ug[0] for ug in user.supitemgroups() if ug[1]]
            perfdatasources = perfdatasources.join(
                    (SUPITEM_GROUP_TABLE, SUPITEM_GROUP_TABLE.c.idsupitem == \
                        Host.idhost),
                ).filter(SUPITEM_GROUP_TABLE.c.idgroup.in_(user_groups))

        perfdatasources = perfdatasources.all()
        return dict(results=[ds.name for ds in perfdatasources])

    class GraphSchema(schema.Schema):
        """Schéma de validation de la méthode default."""
        graphname = validators.UnicodeString()
        host = validators.UnicodeString()
        partial = validators.StringBool(if_missing=False)
        noCache = validators.UnicodeString(if_missing=None)

    @validate(validators=GraphSchema())
    @expose('json')
    def graph(self, graphname, host, partial, noCache):
        """
        Auto-compléteur pour les noms des graphes.

        @param graphname: Motif qui doit apparaître dans le nom du graphe.
        @type graphname: C{unicode}
        @param host: Nom de l'hôte auquel le graphe doit être rattaché.
        @type host: C{unicode}
        @return: Un dictionnaire dont la clé 'results' contient la liste
            des noms des graphes portant sur L{host}, correspondant
            au motif donné et auxquels l'utilisateur a accès.
        @rtype: C{dict}
        """
        graphname = sql_escape_like(graphname)
        user = get_current_user()
        if not user:
            return dict(results=[])

        if partial:
            graphname += '%'

        graphs = DBSession.query(
                Graph.name
            ).distinct(
            ).join(
                (GRAPH_PERFDATASOURCE_TABLE,
                    GRAPH_PERFDATASOURCE_TABLE.c.idgraph == Graph.idgraph),
                (PerfDataSource, PerfDataSource.idperfdatasource ==
                    GRAPH_PERFDATASOURCE_TABLE.c.idperfdatasource),
                (Host, Host.idhost == PerfDataSource.idhost),
            ).filter(Graph.name.ilike(graphname)
            ).filter(Host.name == host
            ).order_by(Graph.name)

        is_manager = in_group('managers').is_met(request.environ)
        if not is_manager:
            user_groups = [ug[0] for ug in user.supitemgroups() if ug[1]]
            graphs = graphs.join(
                    (SUPITEM_GROUP_TABLE, SUPITEM_GROUP_TABLE.c.idsupitem == \
                        Host.idhost),
                ).filter(SUPITEM_GROUP_TABLE.c.idgroup.in_(user_groups))

        graphs = graphs.all()
        return dict(results=[g.name for g in graphs])
