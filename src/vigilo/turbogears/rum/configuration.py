# -*- coding: utf-8 -*-
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Gère différents aspects de la configuration de Rum."""

from tg.i18n import get_lang
from tg import config, request

from rum.templating.genshi_renderer import GenshiRenderer, add_lang_attrs
from genshi.template import TemplateLoader
from genshi.filters import Translator
from tw import framework as tw_framework
from paste.deploy.converters import asbool

from pkg_resources import resource_filename, resource_listdir, resource_isdir
import gettext
import os.path

from vigilo.turbogears.rum.translator import VigiloRumTranslator
from vigilo.models.session import DBSession

# vigilo.turbogears.rum.query n'est pas utilisé directement,
# mais son import permet d'enregistrer la classe VigiloQuery
# qui surcharge une partie du comportement standard de rum.
from vigilo.turbogears.rum import query

class RumGenshiRenderer(GenshiRenderer):
    """
    Version personnalisée du générateur de rendu de Rum.
    Par rapport à la version fournie par Rum, on ajoute un traducteur
    pour les templates de sorte que l'interface d'administration s'affiche
    elle aussi dans la langue de l'utilisateur.
    """

    method = GenshiRenderer.method

    def __init__(self, search_path=None, auto_reload=True, cache_dir=None,
                method=method):
        """Initialise le moteur de rendu."""

        super(RumGenshiRenderer, self).__init__(
            search_path, auto_reload, cache_dir, method)

        # La classe GenshiRenderer définit cette variable avec un chargeur
        # de modèles qui comporte un filtre pour ajouter l'attribut "lang".
        # On écrase ce chargeur pour le remplacer par un qui a le même
        # traitement mais qui ajoute aussi un traducteur.
        self.loader = TemplateLoader(
            search_path=self.search_path,
            auto_reload=self.auto_reload,
            callback=self.__setup_filters,
        )

        # On configure la classe pour que les traductions
        # de vigilo.themes soient utilisées pour traduire
        # les templates utilisés par Rum.
        i18n_dir = resource_filename('vigilo.themes.i18n', '')
        lang = get_lang()

        if lang is None:
            self.__tpl_translator = gettext.NullTranslations()
        else:
            self.__tpl_translator = gettext.translation(
                'vigilo-themes', i18n_dir, lang, fallback=True)

    def __setup_filters(self, tpl):
        """
        Ajoute des filtres au chargeur de modèles.
        Les filtres ajoutés permettent de traduire les modèles (il s'agira
        du premier filtres appelé) et d'ajouter un attribut "lang" sur la
        balise <html> avec la langue de l'utilisateur (idée copiée de Rum).
        """
        # Insertion des filtres dans Genshi :
        # - un filtre pour gérer les traductions dans les templates,
        # - un filtre pour ajouter l'attribut xml:lang aux pages.
        tpl.filters.insert(0, Translator(self.__tpl_translator.ugettext))
        tpl.filters.insert(1, add_lang_attrs)

    def render(self, data, possible_templates=[]):
        # Force l'utilisation de genshi pour le rendu des templates.
        tw_framework.default_view = 'genshi'
        data_copy = data.copy()
        data_copy['asbool'] = asbool
        return super(RumGenshiRenderer, self).render(data_copy, possible_templates)

def get_rum_config(model):
    """Renvoie un dictionnaire avec la configuration à passer à Rum."""

    base_tpl_dir = resource_filename('vigilo.themes.templates', '')

    # On récupère la liste des langues supportées par l'utilisateur,
    # en éliminant les langues au format xx_YY ou xx-YY car rum ne
    # les supporte pas.
    locales = [locale for locale in request.accept_language.best_matches()
                if locale.find('-') < 0 and locale.find('_')]

    rum_config = {
        'rum.repositoryfactory': {
            'session_factory': DBSession,
            'models': model,
        },
        'templating': {
            'renderer': 'vigilo',
            'search_path': [
                os.path.join(base_tpl_dir, config.app_name.lower(), 'admin'),
                os.path.join(base_tpl_dir, config.app_name.lower()),
                os.path.join(base_tpl_dir, 'common'),
            ],
        },
        'rum.translator': {
            'use': VigiloRumTranslator,
            'locales': locales,
        }
    }

    return rum_config
