# -*- coding: utf-8 -*-
"""
Ce module agit comme un proxy qui va interroger les interfaces de
Nagios/RRDgraph et renvoyer le résultat pour qu'il puisse être
affiché dans Vigilo.
"""

import urllib, urllib2, urlparse, logging
from tg import request, expose, config, response
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

def make_proxy_controller(base_controller, server_type, mount_point):
    """
    Factory pour le contrôleur du proxy Nagios/RRDgraph.
    
    @param base_controller: Objet BaseController de l'application
        qui désire monter ce contrôleur dans son arborescence.
    @type base_controller: C{BaseController}
    @param server_type: Type d'application à "proxifier", il peut
        s'agir de "nagios" ou "rrdgraph".
    @param mount_point: URL à laquelle le contrôleur est montée
        (par rapport au RootController de l'application).
        Ce paramètre est utilisé pour réécrire correctement les
        liens absolus générés par Nagios.
    @type mount_point: C{basestring}
    @return: Instance du contrôleur agissant comme un proxy
        vers Nagios/RRDgraph.
    @rtype: C{ProxyController}
    """

    server_type = u'' + server_type.lower()

    # On s'assure que mount_point commence et se termine par un '/'.
    if mount_point[0] != '/':
        mount_point[:0] = '/'
    if mount_point[-1] != '/':
        mount_point = mount_point + '/'

    class ProxyController(base_controller):
        """
        Contrôleur agissant comme un proxy vers Nagios ou RRDgraph.
        """

        # L'accès à ce contrôleur nécessite d'être identifié.
        allow_only = not_anonymous(l_("You need to be authenticated"))

        def _get_server(self, host):
            """
            Étant donné le nom d'un hôte du parc, cette méthode
            renvoie le nom de domaine qualifié (FQDN) du serveur
            de type C{server_type} responsable de cet hôte.

            @param host: Nom d'hôte.
            @type host: C{unicode}

            @return: FQDN du serveur du type demandé responsable de cet hôte.
            @rtype: C{unicode}
            """
            return DBSession.query(
                        VigiloServer.name
                    ).filter(VigiloServer.idvigiloserver == \
                        Ventilation.idvigiloserver
                    ).filter(Ventilation.idhost == Host.idhost
                    ).filter(Ventilation.idapp == Application.idapp
                    ).filter(Host.name == host
                    ).filter(Application.name == server_type
                    ).scalar()

        @expose(content_type=CUSTOM_CONTENT_TYPE)
        def default(self, host, *args, **kwargs):
            """
            Cette méthode capture toutes les requêtes HTTP transmises
            au contrôleur puis les redirige vers le serveur Nagios ou
            RRDgraph (selon le paramètre C{server_type} donné à la factory)
            responsable de l'hôte L{host}.

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

            # On regarde si l'utilisateur a accès à l'hôte demandé.
            perm = DBSession.query(
                        SupItemGroup.idgroup,
                    ).join(
                        (SUPITEM_GROUP_TABLE, SUPITEM_GROUP_TABLE.c.idgroup ==
                            SupItemGroup.idgroup),
                    ).outerjoin(
                        (LowLevelService, LowLevelService.idservice ==
                            SUPITEM_GROUP_TABLE.c.idsupitem),
                    ).filter(SUPITEM_GROUP_TABLE.c.idgroup.in_(supitemgroups))

            # Si en plus on a demandé un service particulier,
            # alors on vérifie les permissions de l'utilisateur
            # sur ce service.
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

            # On traite le cas où l'utilisateur n'a pas les droits requis.
            if perm.scalar() is None:
                if service is not None:
                    LOGGER.warning(l_('Access denied to host "%(host)s" and '
                                    'service "%(service)s"') % {
                        'host': host,
                        'service': service,
                    })
                else:
                    LOGGER.warning(l_('Access denied to host "%s"') % host)
                raise HTTPForbidden()

            # On vérifie que l'hôte est effectivement pris en charge.
            # ie: qu'un serveur du parc héberge l'application server_type
            # responsable de cet hôte.
            vigilo_server = self._get_server(host)
            if vigilo_server is None:
                LOGGER.warning(l_('No %(server_type)s server configured to '
                                'monitor "%(host)s"') % {
                    'server_type': server_type,
                    'host': host,
                })
                raise HTTPNotFound()

            # Préparation des paramètres pour la requête finale.
            kwargs['host'] = host
            data = urllib.urlencode(kwargs)
            args = list(args)

            # TurboGears supprime l'extension de la requête
            # car il peut effectivement des traitements différents
            # à partir d'une même méthode (ex: rendu HTML ou JSON).
            # On la réintègre dans les paramètres pour que les
            # fichier .css ou .js puissent être proxifiés correctement.
            if pylons.request.response_ext and args:
                args[-1] = args[-1] + pylons.request.response_ext

            # Récupére les informations sur l'emplacement de l'application
            # distante. Par défaut, on suppose que la connexion se fait en
            # texte clair (http) sur le port standard (80).
            app_path = config['app_path.%s' % server_type]
            app_scheme = config.get('app_scheme.%s' % server_type, 'http')
            app_port = config.get('app_port.%s' % server_type, 80)
            app_port = int(app_port)

            full_url = [app_scheme,
                        "%s:%d" % (vigilo_server, app_port),
                        "/%s/%s" % (app_path, '/'.join(args)),
                        data,
                        ""]
            full_url = urlparse.urlunsplit(full_url)

            # Facilite la traçabilité sur le serveur distant.
            headers = {
                'X-Forwarded-For': request.remote_addr,
            }

            # On recopie l'en-tête HTTP "Accept" du navigateur.
            # Nagios utilise par exemple cet en-tête pour effectuer
            # de la négociation de contenu sur certaines pages
            # (pour afficher un graphe si Accept = "image/*" ou une
            # page HTML avec une représentation équivalente sinon).
            if pylons.request.accept:
                headers['Accept'] = pylons.request.accept.header_value

            req = urllib2.Request(full_url, headers=headers)
            res = urllib2.urlopen(req)

            # On recopie les en-têtes de la réponse du serveur distant
            # dans notre propre réponse. Cette étape est particulièrement
            # utile lorsque le type MIME du résultat n'est pas "text/html".
            info = res.info()
            for k, v in info.items():
                response.headers[k] = v

            doc = res.read()
            # Pour les documents HTML, on effectue une réécriture
            # des URLs de la page pour que tout passe par le proxy.
            if info['Content-Type'] == 'text/html':
                orig_url = config['app_path.%s' % server_type]
                # Le str() est obligatoire, sinon exception 
                # "AttributeError: You cannot access Response.unicode_body unless charset is set"
                dest_url = str('%s%s/' % (tg.url(mount_point), host))
                doc = doc.replace(orig_url, dest_url)
            return doc

    return ProxyController()

