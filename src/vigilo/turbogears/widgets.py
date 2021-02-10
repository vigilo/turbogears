# -*- coding: utf-8 -*-
# Copyright (C) 2006-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
"""
Validateur et convertisseur de dates selon un format.
"""
from formencode.api import FancyValidator, Invalid
from datetime import datetime

from tg.i18n import ugettext as _, get_lang
import tw2.forms as twf
from tw2.forms.calendars import calendar_css, calendar_js, calendar_setup
try:
    from tw2.forms.calendars import calendar_langs
except ImportError:
    calendar_langs = None


class ExampleDateFormat(object):
    """
    Une classe permettant d'obtenir un exemple de date
    correspondant au format de la locale de l'utilisateur.
    """
    def __str__(self):
        """
        Retourne l'heure courante au format attendu,
        encodée en UTF-8.

        @return: Heure courante au format attendu (en UTF-8).
        @rtype: C{str}
        """
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        """
        Retourne l'heure courante au format attendu.

        @return: Heure courante au format attendu.
        @rtype: C{unicode}
        """
        format = get_date_format()
        date = datetime.strftime(datetime.utcnow(), format).decode('utf-8')
        return _('Eg. %(date)s') % {'date': date}


def get_calendar_lang():
    import tg

    # TODO: Utiliser le champ "language" du modèle pour cet utilisateur ?
    # On récupère la langue du navigateur de l'utilisateur
    lang = get_lang()
    if not lang:
        lang = tg.config['lang']
    else:
        lang = lang[0]

    # TODO: Il faudrait gérer les cas où tout nous intéresse dans "lang".
    # Si l'identifiant de langage est composé (ex: "fr_FR"),
    # on ne récupère que la 1ère partie.
    lang = lang.replace('_', '-')
    lang = lang.split('-')[0]
    return lang


def get_date_format():
    # @HACK: nécessaire car l_() retourne un object LazyString
    # qui n'est pas sérialisable en JSON.
    # TRANSLATORS: Format de date et heure Python/JavaScript.
    # TRANSLATORS: http://www.dynarch.com/static/jscalendar-1.0/doc/html/reference.html#node_sec_5.3.5
    # TRANSLATORS: http://docs.python.org/release/2.5/lib/module-time.html
    return _('%Y-%m-%d %I:%M:%S %p').encode('utf-8')


class DateFormatConverter(FancyValidator):
    """
    Valide une date selon un format identique à ceux
    acceptés par la fonction strptime().
    """
    messages = {
        'invalid': 'Invalid value',
    }
    if_missing = None

    def _convert_to_python(self, value, state):
        if not isinstance(value, basestring):
            raise Invalid(self.message('invalid', state), value, state)

        str_date = value.lower()
        if isinstance(str_date, unicode):
            str_date = str_date.encode('utf-8')

        try:
            # On tente d'interpréter la saisie de l'utilisateur
            # selon un format date + heure.
            date = datetime.strptime(str_date, get_date_format())
        except ValueError:
            try:
                # 2è essai : on essaye d'interpréter uniquement une date.
                # TRANSLATORS: Format de date Python/JavaScript.
                # TRANSLATORS: http://www.dynarch.com/static/jscalendar-1.0/doc/html/reference.html#node_sec_5.3.5
                # TRANSLATORS: http://docs.python.org/release/2.5/lib/module-time.html
                date = datetime.strptime(str_date, _('%Y-%m-%d').encode('utf8'))
            except ValueError:
                raise Invalid(self.message('invalid', state), value, state)
        return date

    def _convert_from_python(self, value, state):
        if not isinstance(value, datetime):
            raise Invalid(self.message('invalid', state), value, state)

        # Même format que pour _to_python.
        return datetime.strftime(value, get_date_format()).decode('utf-8')


class CalendarDateTimePicker(twf.CalendarDateTimePicker):
    validator = DateFormatConverter
    attrs = {
        # Affiche un exemple de date au survol
        # et en tant qu'indication (placeholder).
        'title': ExampleDateFormat(),
        'placeholder': ExampleDateFormat()
    }

    @classmethod
    def post_define(cls):
        cls.resources = [calendar_css, calendar_js, calendar_setup]

    def prepare(self):
        self.calendar_lang = get_calendar_lang()
        self.date_format = get_date_format()
        res = twf.CalendarDateTimePicker.prepare(self)

        # The API around calendars changed a lot between tw2.forms 2.1 & 2.2.
        # We try to make the code work with both versions.
        if calendar_langs:
            # In tw2.forms >= 2.2, the language file is added at definition time.
            # However, we use dynamic language detection, so we must overwrite
            # the resources in post_define() and inject the language file here.
            self.resources.append(calendar_langs[self.calendar_lang])
        return res
