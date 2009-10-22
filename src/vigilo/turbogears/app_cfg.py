# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
"""
Definit la classe chargée de gérer la configuration des applications
utilisant Turbogears sur Vigilo.
"""

__all__ = ('VigiloAppConfig', )

from tg.configuration import AppConfig

class VigiloAppConfig(AppConfig):
    """On modifie AppConfig selon nos besoins."""

    def __init__(self, app_name):
        """Crée une nouvelle configuration."""
        super(VigiloAppConfig, self).__init__()
        self.__app_name = app_name
        self.__tpl_translator = None

    def __setup_template_translator(self):
        """Crée un traducteur pour les modèles (templates)."""
        from pkg_resources import resource_filename
        import gettext
        from tg.i18n import get_lang

        if self.__tpl_translator is None:
            i18n_dir = resource_filename('vigilo.themes', 'i18n')

            # During unit tests, no language is defined which results
            # in an error when get_lang() is called.
            lang = get_lang()
            if lang is None:
                self.__tpl_translator = gettext.NullTranslations()
            else:                
                self.__tpl_translator = gettext.translation(
                    'theme', i18n_dir, lang)

    def setup_paths(self):
        """
        Surcharge pour modifier la liste des dossiers dans lesquels Genshi
        va chercher les templates, afin de supporter un système de thèmes.
        """
        super(VigiloAppConfig, self).setup_paths()
        from pkg_resources import resource_filename

        app_templates = resource_filename(
            'vigilo.themes.templates', self.__app_name)
        common_templates = resource_filename(
            'vigilo.themes.templates', 'common')
        self.paths['templates'] = [app_templates, common_templates]

    def setup_genshi_renderer(self):
        """
        Surcharge pour utiliser un traducteur personnalisé dans les
        modèles (templates).
        """
        # On reprend plusieurs éléments de "tg.configuration".
        from genshi.template import TemplateLoader
        from genshi.filters import Translator
        from tg.render import render_genshi
        from pkg_resources import resource_filename
        from tg.configuration import config

        def template_loaded(template):
            """Appelé lorsqu'un modèle finit son chargement."""
            self.__setup_template_translator()
            template.filters.insert(0, Translator(self.__tpl_translator.ugettext))

        def my_render_genshi(template_name, template_vars, **kwargs):
            """Ajoute une fonction l_ dans les modèles pour les traductions."""
            self.__setup_template_translator()
            template_vars['l_'] = self.__tpl_translator.ugettext
            return render_genshi(template_name, template_vars, **kwargs)

        loader = TemplateLoader(search_path=self.paths.templates,
                                auto_reload=self.auto_reload_templates,
                                callback=template_loaded)

        config['pylons.app_globals'].genshi_loader = loader
        self.render_functions.genshi = my_render_genshi

    def setup_sqlalchemy(self):
        """
        Turbogears a besoin de configurer la session de base de données.
        Puis normalement, il appelle la fonction init_model() du modèle
        de l'application avec les paramètres de la session.
        Dans notre cas, la session est déjà configurée globalement (dans
        vigilo.models.session), donc cette étape n'est pas nécessaire.
        On inhibe le comportement de Turbogears ici.
        """
        pass

