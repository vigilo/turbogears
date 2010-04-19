# -*- coding: utf-8 -*-
"""
Ce module agit comme un proxy qui va interroger les interfaces de Nagios
et renvoyer le résultat pour qu'il puisse être affiché dans Vigilo.
"""

import urllib, urllib2, logging
from tg import request, expose, config
from tg.controllers import CUSTOM_CONTENT_TYPE
import tg, pylons
from repoze.what.predicates import not_anonymous
from tg.exceptions import HTTPForbidden, HTTPNotFound
from pylons.i18n import lazy_ugettext as l_
from sqlalchemy import or_, and_

from vigilo.models.session import DBSession
from vigilo.models.tables import VigiloServer, Host, Ventilation, Application
from vigilo.models.tables import SupItemGroup, LowLevelService
from vigilo.models.tables.secondary_tables import SUPITEM_GROUP_TABLE
from vigilo.turbogears.helpers import get_current_user

LOGGER = logging.getLogger(__name__)

# pylint: disable-msg=R0201,W0232
# - R0201: méthodes pouvant être écrites comme fonctions (imposé par TG2)
# - W0232: absence de __init__ dans la classe (imposé par TG2)

def make_nagios_proxy_controller(base_controller, mount_point):
    """
    Factory pour le contrôleur du proxy Nagios.
    
    @param base_controller: objet BaseController de l'application
        qui désire monter ce contrôleur dans son arborescence.
    @type base_controller: C{BaseController}
    @param mount_point: URL à laquelle le contrôleur est montée
        (par rapport au RootController de l'application).
        Ce paramètre est utilisé pour réécrire correctement les
        liens absolus générés par Nagios.
    @type mount_point: C{basestring}
    @return: Instance du contrôleur agissant comme un proxy vers Nagios.
    @rtype: C{NagiosProxyController}
    """

    # On s'assure que mount_point commence et se termine par un '/'.
    if mount_point[0] != '/':
        mount_point[:0] = '/'
    if mount_point[-1] != '/':
        mount_point = mount_point + '/'

    class NagiosProxyController(base_controller):
        """
        Contrôleur agissant comme un proxy vers Nagios..
        """

        # L'accès à ce contrôleur nécessite d'être identifié.
        allow_only = not_anonymous(l_("You need to be authenticated"))

        def _get_server(self, host):
            """
            Étant donné le nom d'un hôte du parc, cette méthode
            renvoie l'URL du serveur Nagios qui supervise cet hôte.

            @param host: Nom d'hôte.
            @type host: C{str}

            @return: URL du serveur Nagios qui supervise cet hôte.
            @rtype: C{str}
            """
            return DBSession.query(
                        VigiloServer.name
                    ).filter(VigiloServer.idvigiloserver == \
                        Ventilation.idvigiloserver
                    ).filter(Ventilation.idhost == Host.idhost
                    ).filter(Ventilation.idapp == Application.idapp
                    ).filter(Host.name == host
                    ).filter(Application.name == 'nagios'
                    ).scalar()

        @expose(content_type=CUSTOM_CONTENT_TYPE)
        def default(self, host, *args, **kwargs):
            """
            Cette méthode capture toutes les requêtes HTTP transmises
            au contrôleur puis les redirige vers le serveur Nagios
            qui supervise l'hôte L{host}.

            Si ce contrôleur est monté dans "/nagios/", un appel à
            "http://localhost/nagios/example.com/cgi-bin/status.cgi?a=b"
            affichera la page de statut de Nagios concernant l'hôte
            "example.com".
            
            Les paramètres de la requête (query string) sont automatiquement
            transmis dans la requête au serveur Nagios (en POST).
            
            @param host: Nom de l'hôte du parc sur lequel on souhaite
                obtenir des informations.
            @type host: C{unicode}
            @param args: Chemins additionnels de la requête (par exemple,
                ['cgi-bin', 'status.cgi'] avec la requête ci-dessus).
            @type args: C{list}
            @param kwargs: Paramètres additionnels de la requête
                (le contenu de la query string).
            @type kwargs: C{dict}
            """

            user = get_current_user()
            supitemgroups = user.supitemgroups(False)

            # On vérifie qu'il existe effectivement un hôte portant ce nom
            # et configuré pour être supervisé par Vigilo.
            idhost = DBSession.query(
                        Host.idhost
                    ).filter(Host.name == host
                    ).scalar()
            if idhost is None:
                LOGGER.warning(l_('No such monitored host: %s') % host)
                raise HTTPNotFound()

            # Éventuellement, l'utilisateur demande une page
            # qui se rapporte à un service particulier.
            service = kwargs.get('service')

            # On regarde si l'utilisateur a accès à l'hôte
            # et/ou au service demandé.
            perm = DBSession.query(
                        SupItemGroup.idgroup,
                    ).join(
                        (SUPITEM_GROUP_TABLE, SUPITEM_GROUP_TABLE.c.idgroup ==
                            SupItemGroup.idgroup),
                    ).outerjoin(
                        (LowLevelService, LowLevelService.idservice ==
                            SUPITEM_GROUP_TABLE.c.idsupitem),
                    ).filter(SUPITEM_GROUP_TABLE.c.idgroup.in_(supitemgroups))

            if service is not None:
                perm = perm.filter(
                            or_(
                                and_(
                                    LowLevelService.idhost == idhost,
                                    LowLevelService.servicename == service,
                                ),
                                SUPITEM_GROUP_TABLE.c.idsupitem == idhost,
                            ),
                        )
            else:
                perm = perm.filter(
                            or_(
                                LowLevelService.idhost == idhost,
                                SUPITEM_GROUP_TABLE.c.idsupitem == idhost,
                            ),
                        )

            perm = perm.scalar()
            if perm is None:
                if service is not None:
                    LOGGER.warning(l_('Access denied to host "%(host)s" and '
                                    'service "%(service)s"') % {
                        'host': host,
                        'service': service,
                    })
                else:
                    LOGGER.warning(l_('Access denied to host "%s"') % host)
                raise HTTPForbidden()

            vigilo_server = self._get_server(host)
            if vigilo_server is None:
                LOGGER.warning(l_('No Nagios server configured to '
                                'monitor "%s"') % host)
                raise HTTPNotFound()

            kwargs['host'] = host
            data = urllib.urlencode(kwargs)

            args = list(args)
            if pylons.request.response_ext and args:
                args[-1] = args[-1] +  pylons.request.response_ext

            full_url = '%s/%s' % (vigilo_server, '/'.join(args))
            headers = {
                'X-Forwarded-For': request.remote_addr,
            }

            if pylons.request.accept:
                headers['Accept'] = pylons.request.accept.header_value

            req = urllib2.Request(full_url, data, headers)
            res = urllib2.urlopen(req)

            info = res.info()
            if info['Content-Type']:
                pylons.request.content_type = info['Content-Type']

            doc = res.read()
            if info['Content-Type'] == 'text/html':
                doc = doc.replace(config['nagios_web_path'], '%s%s/' %
                                    (tg.url(mount_point), host))
            return doc

    return NagiosProxyController()

