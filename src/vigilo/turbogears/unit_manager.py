# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4: 
"""
Contient le gestionnaire d'unités,
capable de représenter une valeur en utilisant
le préfixe de puissance adéquat.
Par exemple, "1000 B" pourra être converti en "1 kB".
"""

class UnitManager(object):
    '''
    Gestion suffixe pour valeur metrologie
    '''

    def convert_with_unit(self, value):
        '''
        Conversion valeur avec suffixe multiplication
        (cf http://fr.wikipedia.org/wiki/Kilo et autres)

        @param value : valeur
        @type value : valeur numérique

        @return : valeur
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

        @return : valeur
        @rtype : C{str}
        '''

        result = 'Indetermine'
        if maxvalue != 0:
            percentvalue = ( value * 100 / maxvalue)
            result = str(percentvalue) + '%'

        return result

