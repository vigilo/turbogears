# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
"""
Definit la classe chargée de gérer la configuration des applications
utilisant Turbogears sur Vigilo.
"""

from pkg_resources import resource_filename, working_set, get_distribution
import gettext

from tg.configuration import AppConfig, config
from tg.i18n import get_lang
from tg.render import render_genshi

from genshi.template import TemplateLoader
from genshi.filters import Translator

# Enregistre le codec pour l'encodage des textes dans le code JavaScript.
import codecs
from vigilo.turbogears.js_codec import backslash_search
codecs.register(backslash_search)


__all__ = ('VigiloAppConfig', )

class VigiloAppConfig(AppConfig):
    """On modifie AppConfig selon nos besoins."""

    def __init__(self, app_name):
        """Crée une nouvelle configuration."""
        super(VigiloAppConfig, self).__init__()
        self.app_name = app_name
        self.__tpl_translator = None

        # Pour gérer les thèmes, la notation "pointée" n'est pas utilisée.
        # À la place, on indique le nom complet du template (ex: "index.html")
        # lors de l'appel au décorateur @expose.
        self.use_dotted_templatenames = False

        # On définit cette variable à False. En réalité, le comportement
        # est le même que si elle valait toujours True, sauf que l'on
        # met en place les middlewares nous même pour pouvoir gérer les
        # thèmes (cf. <module>/config/middleware.py dans une application).
        self.serve_static = False

        self.DBSession = None

        # On monkey-patch WebOb pour pouvoir récupérer facilement les
        # messages d'erreur éventuellement saisis par le développeur.
        # Ces messages seront ensuite réutilisés dans le contrôleur
        # d'erreurs de vigilo, pour donner un contexte à l'erreur.
        from webob.exc import WSGIHTTPException, Template
        WSGIHTTPException.html_template_obj = Template('''${body}''')
        WSGIHTTPException.body_template_obj = Template('''${detail}''')

        # Idem pour les messages d'erreurs internes générés via WebError.
        from weberror import errormiddleware as errorware
        # On remplace la fonction qui génère le template par une retournant
        # une chaine vide. Le contrôleur d'erreurs affichera un message par
        # défaut du type "Nous n'avons pas pu traiter votre requête".
        errorware.error_template = lambda head_html, exception, extra: ""

        self.renderers = []
        self.default_renderer = 'genshi'
        self.renderers.append('genshi')

        #Configure the base SQLALchemy Setup
        self.use_sqlalchemy = True

        # version
        self.version = get_distribution(self.app_name).version


    def setup_sa_auth_backend(self):
        """
        Initialisation de la configuration de la base de données.
        On se contente de contourner un bug lié à la compatibilité
        ascendante avec TurboGears 2.0.2 et plus, ainsi qu'un bug
        lié à la manière dont la configuration est créée par TG.
        """
        super(VigiloAppConfig, self).setup_sa_auth_backend()

        # TG 2.0.2+ s'attend à trouver une clé "sa_auth.cookie_secret"
        # dans la config. Mais à cause d'un autre problème inhérent à
        # la config de TG, si on définit cette valeur dans le INI, elle
        # n'apparait pas sous le bon nom. On corrige tout ça ici.
        # Voir aussi : http://old.nabble.com/sa_auth-td26789660.html
        if 'sa_auth.cookie_secret' in config:
            config['sa_auth']['cookie_secret'] = config['sa_auth.cookie_secret']
        self.sa_auth.cookie_secret = config['sa_auth']['cookie_secret']

    def __setup_template_translator(self):
        """Crée un traducteur pour les modèles (templates)."""
        if self.__tpl_translator is None:
            i18n_dir = resource_filename('vigilo.themes.i18n', '')

            try:
                # XXX We should make use of fallback languages.
                self.__tpl_translator = gettext.translation(
                    'vigilo-themes', i18n_dir, get_lang())
            except IOError:
                # During unit tests, no language is defined which results
                # in an error when get_lang() is called.
                # Also, an IOErrpr occurrs when no catalog exists for the
                # given language.
                self.__tpl_translator = gettext.NullTranslations()

    def setup_paths(self):
        """
        Surcharge pour modifier la liste des dossiers dans lesquels Genshi
        va chercher les templates, afin de supporter un système de thèmes.
        """
        super(VigiloAppConfig, self).setup_paths()

        app_templates = resource_filename(
            'vigilo.themes.templates', self.app_name)
        common_templates = resource_filename(
            'vigilo.themes.templates', 'common')

        self.paths['templates'] = [app_templates, common_templates]

        # Spécifique projets
        for ext in self.get("extensions", []):
            for entry in working_set.iter_entry_points(
                                    "vigilo.turbogears.templates", ext):
                self.paths['templates'].insert(0, resource_filename(
                                           entry.module_name, "templates"))


    def setup_genshi_renderer(self):
        """
        Surcharge pour utiliser un traducteur personnalisé dans les
        modèles (templates).
        """
        def template_loaded(template):
            """Appelé lorsqu'un modèle finit son chargement."""
            self.__setup_template_translator()
            template.filters.insert(0, Translator(
                self.__tpl_translator.ugettext))

        def my_render_genshi(template_name, template_vars, **kwargs):
            """Ajoute une fonction l_ dans les modèles pour les traductions."""
            self.__setup_template_translator()

            # Add custom translator to templates.
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
        from pylons import config as pylons_config
        from vigilo.models.configure import configure_db

        engine = configure_db(pylons_config, 'sqlalchemy.',
            pylons_config['db_basename'])
        config['pylons.app_globals'].sa_engine = engine

        from vigilo.models import session
        self.DBSession = session.DBSession
        self.sa_auth.dbsession = self.DBSession

        from vigilo.models import tables

        # what is the class you want to use to search
        # for users in the database
        self.sa_auth.user_class = tables.User

        # what is the class you want to use to search
        # for groups in the database
        self.sa_auth.group_class = tables.UserGroup

        # what is the class you want to use to search
        # for permissions in the database
        self.sa_auth.permission_class = tables.Permission

        # The name "groups" is already used for groups of hosts.
        # We use "usergroups" when referering to users to avoid confusion.
        self.sa_auth.translations.groups = 'usergroups'

