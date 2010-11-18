# -*- coding: utf-8 -*-
"""
Ce module agit comme un proxy qui va interroger les interfaces de
Nagios/VigiRRD et renvoyer le résultat pour qu'il puisse être
affiché dans Vigilo.
"""

import urllib, urllib2, urlparse, logging
import tg, pylons
from tg import request, expose, config, response
from tg.controllers import CUSTOM_CONTENT_TYPE
import tg.exceptions as http_exc
from repoze.what.predicates import in_group
from vigilo.turbogears.helpers import ugettext as _
from sqlalchemy import or_, and_
from paste.deploy.converters import asbool
from urllib2_kerberos import HTTPKerberosAuthHandler

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
        par exemple : "nagios" ou "vigirrd".
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

    def _get_server(idhost):
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
                    (Application, Application.idapp == Ventilation.idapp),
                ).filter(Ventilation.idhost == idhost
                ).filter(Application.name == server_type
                ).scalar()

    service_name = None
    service = None
    if data is not None:
        # Éventuellement, l'utilisateur demande une page
        # qui se rapporte à un service particulier.
        service_name = data.get('service')
        data = urllib.urlencode(data)
        service = DBSession.query(
                Service
            ).filter(Service.servicename == service_name
            ).scalar()

    if headers is None:
        headers = {}

    user = get_current_user()

    # On vérifie qu'il existe effectivement un hôte portant ce nom
    # et configuré pour être supervisé par Vigilo.
    host = DBSession.query(
                Host
            ).filter(Host.name == host
            ).scalar()
    if host is None:
        message = _('No such monitored host: %s') % host.idhost
        LOGGER.warning(message)
        raise http_exc.HTTPNotFound(message)

    # On regarde si l'utilisateur a accès à l'hôte demandé.
    is_manager = in_group('managers').is_met(request.environ)
    if not is_manager:
        # On traite le cas où l'utilisateur n'a pas les droits requis.
        if (service is not None and not service.is_allowed_for(user)) \
            or (not host.is_allowed_for(user)):
            message = None
            if service is not None:
                message = _('Access denied to host "%(host)s" and '
                            'service "%(service)s"') % {
                                'host': host.name,
                                'service': service.servicename,
                            }
            else:
                message = _('Access denied to host "%s"') % host
            LOGGER.warning(message)
            raise http_exc.HTTPForbidden(message)

    # On vérifie que l'hôte est effectivement pris en charge.
    # ie: qu'un serveur du parc héberge l'application server_type
    # responsable de cet hôte.
    vigilo_server = _get_server(host.idhost)
    if vigilo_server is None:
        message = _('No %(server_type)s server configured to '
                    'monitor "%(host)s"') % {
                        'server_type': server_type,
                        'host': host,
                    }
        LOGGER.warning(message)
        raise http_exc.HTTPNotFound(message)

    # Récupére les informations sur l'emplacement de l'application
    # distante. Par défaut, on suppose que la connexion se fait en
    # texte clair (http) sur le port standard (80).
    app_path = config['app_path.%s' % server_type].strip('/')
    app_scheme = config.get('app_scheme.%s' % server_type, 'http')
    app_port = config.get('app_port.%s' % server_type,
        app_scheme == 'https' and 443 or 80)
    app_port = int(app_port)
    url = url.lstrip('/')

    manager_url = [app_scheme,
                    "%s:%d" % (vigilo_server, app_port),
                    app_path + "/",
                    "",
                    ""]
    manager_url = urlparse.urlunsplit(manager_url)

    full_url = [app_scheme,
                "%s:%d" % (vigilo_server, app_port),
                "%s/%s" % (app_path, url),
                "",
                ""]
    full_url = urlparse.urlunsplit(full_url)

    try:
        should_redirect = asbool(config.get('app_redirect.%s' % server_type, False))
    except ValueError:
        LOGGER.error(_('Invalid value for app_redirect.%s, not redirecting.'), server_type)
        should_redirect = False

    if should_redirect:
        raise tg.redirect(full_url)

    LOGGER.info(_("Fetching '%s' through the proxy"), full_url)
    req = urllib2.Request(full_url, data, headers=headers)
    opener = urllib2.build_opener()
    opener.add_handler(HTTPKerberosAuthHandler())

    # Configuration de l'authentification
    # vers un éventuel proxy intermédiaire.
    proxy_auth_method = config.get('app_proxy_auth_method', None)
    proxy_auth_username = config.get('app_proxy_auth_username', None)
    proxy_auth_password = config.get('app_proxy_auth_password', None)
    if proxy_auth_method and proxy_auth_username and \
        proxy_auth_password is not None:
        proxy_auth_method = proxy_auth_method.lower()
        proxy_pass_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        proxy_pass_manager.add_password(
            None, manager_url,
            proxy_auth_username,
            proxy_auth_password)
        if proxy_auth_method == 'basic':
            opener.add_handler(urllib2.ProxyBasicAuthHandler(proxy_pass_manager))
            LOGGER.debug(_('Basic authentification to the proxy.'))
        elif proxy_auth_method == 'digest':
            opener.add_handler(urllib2.ProxyDigestAuthHandler(proxy_pass_manager))
            LOGGER.debug(_('Digest authentification to the proxy.'))

    # Configuration de l'authentification
    # vers le site final (Nagios, VigiRRD, ...).
    final_auth_method = config.get('app_auth_method.%s' % server_type, None)
    final_auth_username = config.get('app_auth_username.%s' % server_type, None)
    final_auth_password = config.get('app_auth_password.%s' % server_type, None)
    if final_auth_method and final_auth_username and \
        final_auth_password is not None:
        final_auth_method = final_auth_method.lower()
        final_pass_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        final_pass_manager.add_password(
            None, manager_url,
            final_auth_username,
            final_auth_password)
        if final_auth_method == 'basic':
            opener.add_handler(urllib2.HTTPBasicAuthHandler(final_pass_manager))
            LOGGER.debug(_('Basic authentification to the website.'))
        elif final_auth_method == 'digest':
            opener.add_handler(urllib2.HTTPDigestAuthHandler(final_pass_manager))
            LOGGER.debug(_('Digest authentification to the website.'))

    try:
        res = opener.open(req)
    except urllib2.HTTPError, e:
        # Permet d'associer les erreurs levées par urllib2
        # à des erreurs reconnues par TurboGears2.
        # On obtient ainsi une page d'erreur plus sympathique.
        errors = {
            '401': http_exc.HTTPForbidden,
            '404': http_exc.HTTPNotFound,
            '503': http_exc.HTTPServiceUnavailable,
        }
        error = errors.get(str(e.code))
        if error is None:
            raise e
        raise error(unicode(e.msg))
    return res


# pylint: disable-msg=R0201,W0232
# - R0201: méthodes pouvant être écrites comme fonctions (imposé par TG2)
# - W0232: absence de __init__ dans la classe (imposé par TG2)

class ProxyController(BaseController):
    """
    Contrôleur agissant comme un proxy vers Nagios ou VigiRRD.
    Ce contrôleur utilise la méthode get_through_proxy de ce module
    pour obtenir les documents.
    """

    def __init__(self, server_type, mount_point, allow_only=None):
        super(ProxyController, self).__init__()
        if allow_only:
            self.allow_only = allow_only

        self.server_type = u'' + server_type.lower()

        # On s'assure que mount_point commence et se termine par un '/'.
        if mount_point[0] != '/':
            mount_point[:0] = '/'
        if mount_point[-1] != '/':
            mount_point = mount_point + '/'
        self.mount_point = mount_point

    # Cette méthode ne semble pas fonctionner correctement lorsque 
    # la requête est de type application/json. 
    # De plus, un @expose('json') engendre plus de problèmes qu'il 
    # n'en résoud. Utilisez get_through_proxy() explicitement pour 
    # ce cas particulier.
    @expose(content_type=CUSTOM_CONTENT_TYPE)
    def default(self, *args, **kwargs):
        """
        Cette méthode capture toutes les requêtes HTTP transmises
        au contrôleur puis les redirige vers le serveur Nagios ou
        VigiRRD (selon le paramètre C{server_type} donné au constructeur)
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
        #
        # Idem pour "Accept-Language" qui permettra de traduire
        # partiellement les graphes de VigiRRD.
        for header in ('accept', 'accept_language'):
            header_obj = getattr(pylons.request, header)
            if header_obj:
                headers[header_obj.header_name] = header_obj.header_value

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
            # La réponse obtenue via le proxy est complète,
            # donc il ne faut pas envoyer un en-tête au client
            # indiquant qu'elle est morcelée.
            if k.lower() == 'transfer-encoding':
                continue
            response.headers[k] = v

        doc = res.read()
        # Pour les documents HTML, on effectue une réécriture
        # des URLs de la page pour que tout passe par le proxy.
        if info['Content-Type'].startswith('text/html'):
            orig_url = config['app_path.%s' % self.server_type]
            # Le str() est obligatoire, sinon exception
            # "AttributeError: You cannot access Response.unicode_body
            #  unless charset is set"
            dest_url = str('%s%s/' % (tg.url(self.mount_point), host))
            doc = doc.replace(orig_url, dest_url)
        return doc
