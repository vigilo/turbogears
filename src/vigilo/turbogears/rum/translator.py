# -*- coding: utf-8 -*-
"""Traducteur personnalisé pour Rum."""

from rum.i18n import RumTranslator
from pylons import i18n

class VigiloRumTranslator(RumTranslator):
    """
    Cette classe fournit un traducteur pour Rum.
    Ici, le traducteur se contente de récupérer les traductions
    fournies par Pylons/TurboGears, de sorte que les traductions
    sont centralisées dans un seul fichier.
    """

    def ugettext(self, msg):
        """
        Traduit un message simple.
        Lisez la documentation du module C{gettext} pour plus d'information.
        """
        orig_translation = super(VigiloRumTranslator, self).ugettext(msg)
        if orig_translation != msg:
            return orig_translation
        return i18n.ugettext(msg)

    def ungettext(self, singular, plural, count):
        """
        Traduit un message en tenant compte des pluriels.
        Lisez la documentation du module C{gettext} pour plus d'information.
        """
        orig_translation = super(VigiloRumTranslator, self).ugettext(
            singular, plural, count)
        if orig_translation != msg:
            return orig_translation
        return i18n.ungettext(singular, plural, count)

