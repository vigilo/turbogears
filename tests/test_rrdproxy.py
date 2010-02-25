# -*- coding: utf-8 -*-
'''
Created on 09 nov. 2009
@author: flaheugu


Tests RRD Proxy
'''

import unittest
import time

from tg import config

from vigilo.turbogears.rrdproxy import RRDProxy
from vigilo.turbogears.rrdproxy import SuffixManager

class TestSuffixManager(unittest.TestCase):
    """ Test Gestion Valeur Metrologie """  
 
    def test_convert_with_suffix(self):
        """ fonction verification conversion suffixe multiplication"""
        suffixmanager = SuffixManager()
    
        value = 5
        result = suffixmanager.convert_with_suffix(value)
        assert(result == '5.0')

        value = 12345.
        result = suffixmanager.convert_with_suffix(value)
        assert(result == '12.345k')

        value = -0.07
        result = suffixmanager.convert_with_suffix(value)
        assert(result == '-7.0c')

    def test_convert_with_percent(self):
        """ fonction verification conversion avec pourcentage"""
        suffixmanager = SuffixManager()
        value = 60
        maxvalue = 100
        result = suffixmanager.convert_to_percent(value, maxvalue)
        assert(result == '60%')

class RRDProxy_without_rrdgraph(RRDProxy):
    """
    Classe de substitution de RRDProxy pour effectuer les tests
    sans rrdgraph
    """
    def __init__(self, content, *args, **kwargs):
        '''Constructeur'''
        super(RRDProxy_without_rrdgraph, self).__init__(*args, **kwargs)
        self.content = content

    def _retrieve_content(self, *args, **kwargs):
        '''Retour - Surcharge'''
        return self.content


class TestRRDProxy(unittest.TestCase):
    """ Test Gestion Valeur Metrologie """  

    def __init__(self, *args, **kwargs):
        '''Constructeur'''
        super(TestRRDProxy, self).__init__(*args, **kwargs)
        #self.url = config.get('rrd_url') -> ne marche pas
        self.url = 'http://localhost'

    def test_last_value(self):
        """ fonction verification derniere valeur"""
        result = None

        server = 'par.linux0'
        indicator = 'IO Reads'

        content = '''<html><head>
        </head><body>
        <p>Please choose one of these servers:</p>
        <ul><li><a href="rrdgraph.py?server=host2">host2</a></li><li>
        <a href="rrdgraph.py?server=localhost">localhost</a></li></ul></body></html>
        '''

        url = self.url
        if url is not None:
            rrdproxy = RRDProxy_without_rrdgraph(content, url)
            result = rrdproxy.get_last_value(server, indicator)

        assert(result != None)

    def test_img(self):
        """ fonction verification image"""
        result = None

        server = 'par.linux0'
        graph = 'Load'
        
        content = '''<html><head>
        </head><body>
        <p>Please choose one of these servers:</p>
        <ul><li><a href="rrdgraph.py?server=host2">host2</a></li><li>
        <a href="rrdgraph.py?server=localhost">localhost</a></li></ul></body></html>'
        '''

        url = self.url
        if url is not None:
            rrdproxy = RRDProxy_without_rrdgraph(content, url)
            result = rrdproxy.get_img(server, graph)

        assert(result != None)

    def test_img_data(self):
        """ fonction verification data image"""
        result = None

        server = 'par.linux0'
        graph = 'Load'
       
        content = '''<html><head>
        </head><body>
        <p>Please choose one of these servers:</p>
        <ul><li><a href="rrdgraph.py?server=host2">host2</a></li><li>
        <a href="rrdgraph.py?server=localhost">localhost</a></li></ul></body></html>
        '''

        url = self.url
        if url is not None:
            rrdproxy = RRDProxy_without_rrdgraph(content, url)
            result = rrdproxy.get_img_data(server, graph)

        assert(result != None)

    def test_img_with_params(self):
        '''fonction vérification get_img_with_params'''
        result = None

        server = 'par.linux0'
        graph = 'Load'
        direct = 1
        duration = 24*3600
        start = int(time.time()) - 24*3600
        details = 1

        content = '''<html><head>
        </head></html>
        '''

        url = self.url
        if url is not None:
            rrdproxy = RRDProxy_without_rrdgraph(content, url)
            result = rrdproxy.get_img_with_params(server, graph, direct, \
            duration, start, details)

        assert(result != None)

    def test_img_name_with_params(self):
        '''fonction vérification get_img_name_with_params'''
        result = None

        server = 'par.linux0'
        graph = 'Load'
        direct = None
        duration = None
        start = None
        details = None

        content = '''<html><head>
        </head></html>
        '''

        url = self.url
        if url is not None:
            rrdproxy = RRDProxy_without_rrdgraph(content, url)
            result = rrdproxy.get_img_name_with_params(server, graph, direct, \
            duration, start, details)

        assert(result != None)

    def test_starttime(self):
        '''fonction vérification starttime'''
        result = None

        server = 'par.linux0'
        getstarttime = 1

        content = '''<html><head>
        </head></html>
        '''

        url = self.url
        if url is not None:
            rrdproxy = RRDProxy_without_rrdgraph(content, url)
            result = rrdproxy.get_starttime(server, getstarttime)

        assert(result != None)
    
    def test_exportCSV(self):
        '''fonction vérification export CSV'''
        result = None

        server = 'par.linux0'
        graph = 'Load'
        indicator = 'All'
        start = None
        end = None

        content = '''<html><head>
        </head></html>
        '''

        url = self.url
        if url is not None:
            rrdproxy = RRDProxy_without_rrdgraph(content, url)
            result = rrdproxy.exportCSV(server, graph, indicator, start, end)

        assert(result != None)


if __name__ == "__main__": 
    unittest.main()
