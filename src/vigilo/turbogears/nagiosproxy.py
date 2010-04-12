# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4: 
"""Gestion Nagios par proxy"""

import urllib
import urllib2

class NagiosProxy(object):
    '''
    Proxy Nagios

    cf http://www.voidspace.org.uk/python/articles/urllib2_francais.shtml
    '''

    def __init__(self, url):
        '''Constructeur'''
        self._url = url

    #def _retrieve_content(self, url, values):
    def _retrieve_content(self, *args, **kwargs):
        '''
        Lecture de donnees Nagios à partir d une url et d un dictionnaire
        ce dictionnaire contient les arguments pour l url
        '''

        handle = None
        result = None

        if kwargs is not None:
            url = kwargs.get('url')
            values = kwargs.get('values')
            if url is not None and values is not None:
                data = urllib.urlencode(values)
                try:
                    handle = urllib2.urlopen(url, data)
                    result = handle.read()
                except urllib2.URLError:
                    raise
                finally:
                    if handle:
                        handle.close()

        return result


    def get_status(self, host):
        '''
        lecture status
     
        @param host : hôte
        @type host : C{str}
        @return : donnees Nagios
        @rtype: 
        '''

        values = {'host' : host,
                  'style' : 'detail',
                  'supNav' : 1}

        url = '%s/%s' % (self._url, 'status.cgi')
        return self._retrieve_content(url=url, values=values)


    def get_extinfo(self, host, service):
        '''
        lecture informations
     
        @param host : hôte
        @type host : C{str}
        @param service : service
        @type service : C{str}
        @return : donnees Nagios
        @rtype: 
        '''

        values = {'host' : host,
                  'service' : service,
                  'type' : 2,
                  'supNav' : 1}

        url = '%s/%s' % (self._url, 'extinfo.cgi')
        return self._retrieve_content(url=url, values=values)
