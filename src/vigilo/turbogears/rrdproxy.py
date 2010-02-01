# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4: 
"""Gestion RRD par proxy"""

import urllib
import urllib2
from HTMLParser import HTMLParser
import os
#from pylons.i18n import ugettext as _


class RRDProxy(object):
    '''
    Proxy RRD

    cf http://www.voidspace.org.uk/python/articles/urllib2_francais.shtml
    '''

    def __init__(self, url):
        '''Constructeur'''
        self._url = os.path.join(url, 'rrdgraph.py')

    def _retrieve_content(self, url, values):
        ''' Lecture du contenu RRD à partir d'un dictionnaire de valeurs'''
        
        handle = None
        result = None
        data = urllib.urlencode(values)
        proxy_handler = urllib2.ProxyHandler({'http': url})
        opener = urllib2.build_opener(proxy_handler)
        try:
            handle = opener.open(url, data)
            result = handle.read()
        except urllib2.URLError, e:
            raise
        finally:
            if handle:
                handle.close()
            
        return result

    def get_last_value(self, server, indicator):
        '''
        lecture derniere valeur de metrologie associee au parametre indicator
     
        @param server : serveur
        @type server : C{str}
        @param indicator : indicateur
        @type indicator : C{str}

        @return :
        @rtype: liste de deux elements
        '''

        values = {'host' : server,
                  'indicator' : indicator}
        
        url = self._url
        url = os.path.join(url, 'outputMetrologie')
        
        return self._retrieve_content(url, values)

    def get_host(self, server):
        '''
        lecture hôte

        @param server : serveur
        @type server : C{str}

        @return :
        @rtype : 
        '''

        values = {'server' : server}
        url = self._url
        
        return self._retrieve_content(url, values)

    def get_img(self, server, graph):
        '''
        lecture image

        @param server : serveur
        @type server : C{str}
        @param graph : graphe
        @type graph : C{str}

        @return :
        @rtype : image
        '''

        values = {'server' : server,
                  'graphtemplate' : graph,
                  'direct' : 1}
        url = self._url        

        return self._retrieve_content(url, values)

    def get_img_url(self, server, graph, urlp):
        '''
        lecture image

        @param server : serveur
        @type server : C{str}
        @param graph : graphe
        @type graph : C{str}

        @return :
        @rtype : image
        '''
        
        values = {'server' : server,
                  'graphtemplate' : graph,
                  'direct' : 1}
        url = urlp
        return self._retrieve_content(url, values)

    def get_img_data(self, server, graph):
        '''
        lecture donnees image : src et alt

        @param server : serveur
        @type server : C{str}
        @param graph : graphe
        @type graph : C{str}

        @return :
        @rtype : C{str}
        '''

        values = {'server' : server,
                  'graphtemplate' : graph,
                  'details' : 0}

        url = self._url
        
        result = self._retrieve_content(url, values)
        if result:
            imghtmlparser = ImgHTMLParser()
            result = imghtmlparser.get_src_alt(result)
            imghtmlparser.close()

        return result

    def get_img_with_params(self, server, graph, direct, duration, start, details):
        '''
        lecture image avec parametres
     
        @param server : serveur
        @type server : C{str}
        @param graph : graphe
        @type graph : C{str}
        @param direct : 
        @type direct : int
        @param start : 
        @type start : int
        @param duration : 
        @type duration : int
        @param details : 
        @type details : int

        @return : image
        @rtype :
        '''

        values = {'server' : server,
                  'graphtemplate' : graph,
                  'direct' : direct,
                  'duration' : duration,
                  'start' : start,
                  'details' : details}
        url = self._url
        return self._retrieve_content(url, values)
    
    def get_img_name_with_params(self, server, graph, direct, duration, start, details):
        '''
        lecture nom image avec parametres
     
        @param server : serveur
        @type server : C{str}
        @param graph : graphe
        @type graph : C{str}
        @param direct : 
        @type direct : int
        @param start : 
        @type start : int
        @param duration : 
        @type duration : int
        @param details : 
        @type details : int

        @return : nom image
        @rtype: C{str}
        '''

        values = {'server' : server,
                  'graphtemplate' : graph,
                  'direct' : direct,
                  'duration' : duration,
                  'start' : start,
                  'details' : details}
        data = urllib.urlencode(values)
        url = self._url
        img_name = url + '?' + data 
        return img_name

    def get_starttime(self, server, getstarttime):
        '''
        lecture valeur temps
     
        @param server : serveur
        @type server : C{str}
        @param getstarttime : 
        @type getstarttime : int

        @rtype:
        '''

        values = {'server' : server,
                  'getstarttime' : getstarttime
                 }
        url = self._url        
        return self._retrieve_content(url, values)
 
    def exportCSV(self, server, graph, indicator=None, start=None, end=None):
        '''
        export CSV
     
        @param server : serveur
        @type server : C{str}
        @param graph : graphe
        @type graph : C{str}
        @param indicator : indicateur graphe
        @type indicator : C{str}
        @param start : debut plage export
        @type start : C{str}
        @param end : fin plage export
        @type end : C{str}

        @return : donnees RRD d apres server, indicateur et plage
        @rtype: C{str}
        '''

        values = {'server' : server,
                  'graphtemplate': graph,
                  'indicator' : indicator,
                  'start' : start,
                  'end' : end
                 }
        url = self._url
        url = os.path.join(url, 'exportCSV')

        return self._retrieve_content(url, values)


class ImgHTMLParser(HTMLParser):
    '''
    Parser HTML

    Analyse texte lu dans RRD pour determination valeurs src et alt
    '''

    def __init__(self):
        HTMLParser.__init__(self)
        self._dr = {}

    def get_src_alt(self, text):
        '''
        Determination valeurs pour src et alt

        @param text : texte a analyser
        @type text : C{str}


        @rtype: dictionnaire
        '''

        self.feed(text)
        return self._dr

    def handle_starttag(self, tag, attrs):
        '''
        Traitement sur debut Tag
        
        @param tag : tag a analyser
        @type tag : C{str}
        @param attrs : attributs pour tag
        @param attrs : C{str}

        @return:  donnees src et alt
        @rtype:  dictionnaire
        '''

        if tag == 'img':
            text = self.get_starttag_text()

            # texte associe a src
            start_sep = 'src="'
            end_sep = '"'
            src = self.get_value(text, start_sep, end_sep)
            
            # texte associe a alt
            start_sep = 'alt="'
            end_sep = '"'
            alt = self.get_value(text, start_sep, end_sep)

            self._dr = { 'src': src, 'alt': alt}

    def handle_endtag(self, tag):
        '''
        Traitement sur fin Tag
        
        @param tag : tag a analyser
        @type tag : C{str}
        '''
        text = ''
        if tag == 'img':
            text = self.get_starttag_text()

    def get_value(self, text, start_sep, end_sep):
        '''
        Determination texte compris entre separateurs debut et fin

        @param start_sep : separateur debut
        @type start_sep : C{str}
        @param end_sep : separateur fin
        @type end_sep : C{str}

        @rtype : C{str}
        '''

        # elements texte
        separator = ' '
        ltext = text.split(separator)

        value = ''
        b_start =  False
        for elt in ltext:
            # separateur debut = debut element
            if elt.startswith(start_sep) == True:
                value = elt[len(start_sep):]
                b_start =  True

                # separateur fin = fin element
                if elt.endswith(end_sep) == True:
                    value = elt[len(start_sep):len(elt)-len(end_sep)]
                    b_start =  False
                    break

            # separateur fin = fin element
            elif elt.endswith(end_sep) == True:
                value_l = elt[:len(elt) -len(end_sep)]
                if value != '':
                    value += separator
                value += value_l
                b_start = False

            # autre
            else:
                if b_start == True:
                    if value != '':
                        value += separator
                    value += elt

        return value


class SuffixManager(object):
    '''
    Gestion suffixe pour valeur metrologie
    '''

    def convert_with_suffix(self, value):
        '''
        Conversion valeur avec suffixe multiplication
        (cf http://fr.wikipedia.org/wiki/Kilo et autres)

        @param value : valeur
        @type value : valeur numérique

        @rtype : C{str}
        '''

        svalue = ''

        # signe
        sign = ''
        if value < 0:
            sign = '-'

        # determination puissance de 10
        value_l = abs(value)
        power_l = 0
        if value_l >= 1:
            svalue = str(int(value_l))
            power_l = len(svalue) - 1
        else:
            svalue = str(value_l)
            power_l = len(svalue) - 2
            power_l =  -power_l

        # data sur puissances de 10 :
        # - pour exposant < 0 : -9, -6, -3, -2, -1
        # - pour exposant = 0 :
        # - pour exposant > 0 : 1, 2, 3, 6, 9
        lpd = []
        lpd.append({'s': 'p', 'p': -9})
        lpd.append({'s': 'µ', 'p': -6})        
        lpd.append({'s': 'm', 'p': -3})
        lpd.append({'s': 'c', 'p': -2})
        lpd.append({'s': 'd', 'p': -1})
        lpd.append({'s': '', 'p': 0})
        lpd.append({'s': 'da', 'p': 1})
        lpd.append({'s': 'h', 'p': 2})
        lpd.append({'s': 'k', 'p': 3})
        lpd.append({'s': 'M', 'p': 6})
        lpd.append({'s': 'G', 'p': 9})

        power_p = None
        suffix_p = None

        power_c = None
        suffix_c = None

        value_l = float(abs(value))
        for elt in lpd:
            power_p = power_c
            suffix_p = suffix_c
            for key in elt.iterkeys():
                if key == 's':
                    suffix_c = elt[key]
                if key == 'p':
                    power_c = elt[key]

            if power_l < power_c:
                if power_p is not None:
                    if power_l >= power_p:
                        value_l /= (10 ** power_p)
                        svalue = sign
                        svalue += str(value_l)
                        svalue += suffix_p

                        break
                else:
                    svalue = sign
                    svalue += str(value_l)
                    break

        return svalue

    def convert_to_percent(self, value, maxvalue):
        '''
        Conversion avec pourcentage

        @param value : valeur
        @type value : int
        @param maxvalue : valeur max
        @type value : int

        @rtype : C{str}
        '''

        result = 'Indetermine'
        if maxvalue != 0:
            percentvalue = ( value * 100 / maxvalue)
            result = str(percentvalue) + '%'

        return result
