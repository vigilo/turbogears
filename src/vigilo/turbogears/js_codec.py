# -*- coding: utf-8 -*-
"""
Fournit un codec capable d'encoder et de décoder les chaines de caractères
avec des backslashes. Le résultat est compatible avec JavaScript.

Exemple d'utilisation:
>>> 'ab"\\\\c'.encode('backslash')
'ab\\\\"\\\\\\\\c'

>>> 'ab\\\\"\\\\\\\\c'.decode('backslash')
'ab"\\\\c'
"""


def encode_backslash(s, errors = 'strict'):
    """Encode les caractères spéciaux de L{s} avec des contre-obliques."""
    return (s.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"'),
        len(s))

def decode_backslash(s, errors = 'strict'):
    """
    Décode la chaine L{s} contenant des caractères spéciaux échappés
    par des contre-obliques.
    """
    return (s.replace('\\\\', '\\').replace("\\'", "'").replace('\\"', '"'),
        len(s))

def backslash_search(encoding):
    """Fonction de recherche de codecs."""
    if encoding == 'backslash':
        return (encode_backslash, decode_backslash, None, None)
    return None

