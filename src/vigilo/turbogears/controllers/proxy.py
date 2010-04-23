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
from pylons.i18n import ugettext as _
from sqlalchemy import or_, and_

from vigilo.models.session import DBSession
from vigilo.models.tables import VigiloServer, Host, Ventilation, Application
from vigilo.models.tables import SupItemGroup, LowLevelService
from vigilo.models.tables.secondary_tables import SUPITEM_GROUP_TABLE

from vigilo.turbogears.helpers import get_current_user
from vigilo.turbogears.controllers import BaseController

LOGGER = logging.getLogger(__name__)

__all__ = ('make_proxy_controller', 'get_through_proxy', )

def get_through_proxy(server_type, host, url, data=None, headers=None):
    """
    Récupère le contenu d'un document à travers le mécanisme de proxy.

    @param server_type: Type d'application à "proxifier",
        par exemple : "nagios" ou "rrdgraph".
    @type server_type: C{basestring}
    @param host: Nom de l'hôte (supervisé) concerné par la demande.
    @type host: C{unicode}
    @param url: URL à demander sur le serveur distant, avec éventuellement
        des paramètres intégrés (query string).
    @type url: C{basestring}
    @param data: Dictionnaire contenant une série de paramètres à transmettre
        dans la requête. Si des paramètres sont donnés, la requête engendrée
        deviendra automatiquement du type POST au lieu de GET.
    @type data: C{dict}
    @param headers: Dictionnaire d'en-têtes HTTP à passer en plus dans la
        requête. Vous pouvez par exemple utiliser l'en-tête 'X-Forwarded-For'
        pour indiquer l'adresse IP de l'utilisateur à l'origine de la requête
        proxifiée (à des fins de traçabilité/imputation).
    @type headers: C{dict}
    @return: Renvoie le résultat de la requête proxifiée, tel que retourné
        par urllib2.
    @rtype: C{file-like}
    """

    def _get_server(hostname):
        """
        Étant donné le nom d'un hôte du parc, cette méthode
        renvoie le nom de domaine qualifié (FQDN) du serveur
        de type C{server_type} responsable de cet hôte.

        @param hostname: Nom d'hôte.
        @type  hostname: C{unicode}

        @return: FQDN du serveur du type demandé responsable de cet hôte.
        @rtype: C{unicode}
        """
        return DBSession.query(
                    VigiloServer.name
                ).join(
                    (Ventilation, Ventilation.idvigiloserver ==
                        VigiloServer.idvigiloserver),
                    (Host, Host.idhost == Ventilation.idhost),
                    (Application, Application.idapp == Ventilation.idapp),
                ).filter(Host.name == hostname
                ).filter(Application.name == server_type
                ).scalar()

    service = None
    if data is not None:
        # Éventuellement, l'utilisateur demande une page
        # qui se rapporte à un service particulier.
        service = data.get('service')
        data = urllib.urlencode(data)

    if headers is None:
        headers = {}

    user = get_current_user()
    supitemgroups = user.supitemgroups(False)

    # On vérifie qu'il existe effectivement un hôte portant ce nom
    # et configuré pour être supervisé par Vigilo.
    idhost = DBSession.query(
                Host.idhost
            ).filter(Host.name == host
            ).scalar()
    if idhost is None:
        message = _('No such monitored host: %s') % host
        LOGGER.warning(message)
        raise HTTPNotFound(message)

    # On regarde si l'utilisateur a accès à l'hôte demandé.
    perm = DBSession.query(
                SupItemGroup.idgroup
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
        message = None
        if service is not None:
            message = _('Access denied to host "%(host)s" and '
                        'service "%(service)s"') % {
                            'host': host,
                            'service': service,
                        }
        else:
            message = _('Access denied to host "%s"') % host
        LOGGER.warning(message)
        raise HTTPForbidden(message)

    # On vérifie que l'hôte est effectivement pris en charge.
    # ie: qu'un serveur du parc héberge l'application server_type
    # responsable de cet hôte.
    vigilo_server = _get_server(host)
    if vigilo_server is None:
        message = _('No %(server_type)s server configured to '
                    'monitor "%(host)s"') % {
                        'server_type': server_type,
                        'host': host,
                    }
        LOGGER.warning(message)
        raise HTTPNotFound(message)

    # Récupére les informations sur l'emplacement de l'application
    # distante. Par défaut, on suppose que la connexion se fait en
    # texte clair (http) sur le port standard (80).
    app_path = config['app_path.%s' % server_type]
    app_scheme = config.get('app_scheme.%s' % server_type, 'http')
    app_port = config.get('app_port.%s' % server_type, 80)
    app_port = int(app_port)

    full_url = [app_scheme,
                "%s:%d" % (vigilo_server, app_port),
                "/%s/%s" % (app_path, url),
                "",
                ""]
    full_url = urlparse.urlunsplit(full_url)

    req = urllib2.Request(full_url, data, headers=headers)
    res = urllib2.urlopen(req)
    return res


# pylint: disable-msg=R0201,W0232
# - R0201: méthodes pouvant être écrites comme fonctions (imposé par TG2)
# - W0232: absence de __init__ dans la classe (imposé par TG2)

class ProxyController(BaseController):
    """
    Contrôleur agissant comme un proxy vers Nagios ou RRDgraph.
    Ce contrôleur utilise la méthode get_through_proxy de ce module
    pour obtenir les documents.
    """

    # L'accès à ce contrôleur nécessite d'être identifié.
    allow_only = not_anonymous(_("You need to be authenticated"))

    def __init__(self, server_type, mount_point):
        super(ProxyController, self).__init__()
        self.server_type = u'' + server_type.lower()

        # On s'assure que mount_point commence et se termine par un '/'.
        if mount_point[0] != '/':
            mount_point[:0] = '/'
        if mount_point[-1] != '/':
            mount_point = mount_point + '/'
        self.mount_point = mount_point

    @expose(content_type=CUSTOM_CONTENT_TYPE)
    def default(self, *args, **kwargs):
        """
        Cette méthode capture toutes les requêtes HTTP transmises
        au contrôleur puis les redirige vers le serveur Nagios ou
        RRDgraph (selon le paramètre C{server_type} donné au constructeur)
        responsable de l'hôte donné.

        Si ce contrôleur est monté dans "/nagios/", un appel à
        "http://localhost/nagios/example.com/cgi-bin/status.cgi?a=b"
        affichera la page de statut de Nagios concernant l'hôte
        "example.com".
        
        Les paramètres de la requête (query string) sont automatiquement
        transmis dans la requête au serveur distant (en POST).

        @param args: Parties du chemin. Si le dernier élément du chemin
            de la requête possèdait une extension, elle est supprimée
            par TurboGears et n'apparaît pas ici. Le premier élément
            du chemin DOIT être le nom d'hôte vers lequel on proxifie.
        @type args: C{tuple}
        @param kwargs: Paramètres additionnels de la requête
            (ie: la query string, sous forme de dictionnaire).
            Ils seront passés en POST dans la requête proxifiée.
        @type kwargs: C{dict}
        """
        host = args[0]
        args = list(args[1:])

        # TurboGears supprime l'extension de la requête
        # car il peut effectivement des traitements différents
        # à partir d'une même méthode (ex: rendu HTML ou JSON).
        # On la réintègre dans les paramètres pour que les
        # fichier .css ou .js puissent être proxifiés correctement.
        if pylons.request.response_ext and args:
            args[-1] = args[-1] + pylons.request.response_ext


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

        url = '/'.join(args)
        if pylons.request.GET:
            url = '%s?%s' % (url, urllib.urlencode(pylons.request.GET))
        post_data = None
        if pylons.request.POST:
            post_data = pylons.request.POST
        res = get_through_proxy(self.server_type,
            host, url, post_data, headers)

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
            orig_url = config['app_path.%s' % self.server_type]
            # Le str() est obligatoire, sinon exception 
            # "AttributeError: You cannot access Response.unicode_body
            #  unless charset is set"
            dest_url = str('%s%s/' % (tg.url(self.mount_point), host))
            doc = doc.replace(orig_url, dest_url)
        return doc

