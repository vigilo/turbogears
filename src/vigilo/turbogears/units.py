# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4: 
"""
Contient le gestionnaire d'unités,
capable de représenter une valeur en utilisant
le préfixe de puissance adéquat.
Par exemple, "1000 B" pourra être converti en "1 kB".
"""

SUFFIXES = [
       (-9, "p"),
       (-6, "µ"),
       (-3, "m"),
       ( 0, "" ),
       ( 3, "k"),
       ( 6, "M"),
       ( 9, "G"),
       (12, "T"),
       (15, "P"),
   ]

def convert_with_unit(value, digits=3):
    '''
    Conversion valeur avec suffixe multiplication
    (cf http://fr.wikipedia.org/wiki/Kilo et autres)

    @param value : valeur
    @type value : C{float}

    @return : valeur
    @rtype : C{str}
    '''

    power, suffix = _get_value_suffix(value)
    if power is None or suffix is None:
        return _get_digits(value, digits)

    value = value / (10 ** power)
    if str(value).endswith(".0"):
        value = int(value)
    value = _get_digits(value, digits)
    return "%s%s" % (value, suffix)


def _get_value_suffix(value):
    # determination puissance de 10
    value = abs(value)
    power = 0
    if value >= 1:
        svalue = str(int(value))
        power = len(svalue) - 1
    else:
        svalue = str(value)
        power = len(svalue) - 2
        power = -power

    value = float(value)
    if power < SUFFIXES[0][0]:
        # Pas d'unité, on laisse Python faire : il va faire de la notation
        # exponentielle type '4.2e-10'
        return (None, None)
    for index, pow_suff in enumerate(SUFFIXES):
        cur_power, cur_suffix = pow_suff
        if cur_power <= power:
            continue
        # On prend le dernier: celui qu'on vient juste de dépasser
        return SUFFIXES[index - 1]

def _get_digits(value, digits=3):
    #print "in:", value
    if len(str(abs(value))) <= digits:
        return value
    if abs(value) < 1:
        main = str(abs(value))[:digits+2]
    elif str(abs(value)).count(".") and str(abs(value)).index(".") < digits:
        main = str(abs(value))[:digits+1]
    else:
        main = str(abs(value))[:digits]
    if value < 0:
        main = "-%s" % main
    #print "out:", main
    return main