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
    if mount_point[0] != '/':
        mount_point[:0] = '/'
    if mount_point[-1] != '/':
        mount_point = mount_point + '/'

    class NagiosProxyControllerHelper(base_controller):
        def _get_server(self, host):
            """
            Determination Serveur Nagios pour l hote courant
            (Server Nagios -> nom de l application associee = nagios)

            @param host: hôte
            @type host: C{str}

            @return: serveur Nagios qui supervise cet hôte.
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

    return NagiosProxyControllerHelper()

