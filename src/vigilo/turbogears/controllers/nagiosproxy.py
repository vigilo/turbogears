# -*- coding: utf-8 -*-
"""
Ce module agit comme un proxy qui va interroger les interfaces de Nagios
et renvoyer le résultat pour qu'il puisse être affiché dans Vigilo.
"""

import urllib, urllib2
from tg import request, expose, config
from tg.controllers import CUSTOM_CONTENT_TYPE
import tg, pylons

from vigilo.models.session import DBSession
from vigilo.models.tables import VigiloServer, Host, Ventilation, Application

class NoNagiosServerConfigured(Exception):
    """
    Exception levée lorsqu'aucun serveur Nagios configuré
    pour un hôte donné n'a pu être trouvé.
    """

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

            vigilo_server = self._get_server(host)
            if vigilo_server is None:
                raise NoNagiosServerConfigured()

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

