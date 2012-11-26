# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Definit la classe chargée de gérer la configuration des applications
utilisant Turbogears sur Vigilo.
"""

import os
import gettext
import codecs
from pkg_resources import resource_filename, working_set, get_distribution
from paste.deploy.converters import asbool
from logging import getLogger

from routes.middleware import RoutesMiddleware
from beaker.middleware import SessionMiddleware, CacheMiddleware
from tg.configuration import AppConfig, config
from tg.i18n import get_lang
from tg.render import render_genshi

from pkg_resources import parse_version
from genshi import __version__ as genshi_version
from pylons import config as pylons_config
from genshi.template import TemplateLoader
from genshi.filters import Translator
from vigilo.turbogears.js_codec import backslash_search

from webob import Response
from tw.core.resources import _FileIter

# Middleware d'authentification adapté à nos besoins.
from vigilo.turbogears.repoze.middleware import make_middleware_with_config

# Enregistre le codec pour l'encodage des textes dans le code JavaScript.
codecs.register(backslash_search)

# Ajoute le support de la mise en cache par le navigateur
# pour les ressources statiques servies par ToscaWidgets.
old_func = Response.cache_expires
def cache_expires(self, seconds=0, **kw):
    """
    Surcharge la méthode "cache_expires" native
    pour pouvoir envoyer un en-tête "Last-Modified"
    qui permet d'avoir des réponses conditionnées
    en fonction de l'en-tête "If-Modified-Since".

    Cette méthode n'est appelée que par ToscaWidgets,
    lorsque le paramètre "toscawidgets.resources_expire"
    est positionné dans la configuration.
    Voir L{VigiloAppConfig.add_tosca_middleware} pour plus
    d'informations.

    @param seconds: Nombre de secondes durant lequel la ressource
        peut être réutilisée depuis le cache du navigateur.
    """
    # Pour garder le comportement par défaut
    # (positionnement des en-têtes relatifs au cache).
    old_func(self, seconds, **kw)

    # On essaye de trouver un objet file-like
    # qui servira pour déterminer la date de
    # dernière modification de la ressource.
    if isinstance(self.app_iter, _FileIter):
        stream = self.app_iter.fileobj
    else:
        stream = self.app_iter

    # Si un tel objet a été trouvé, on ajoute
    # en en-tête sa date de dernière modification.
    if isinstance(stream, file):
        try:
            self.last_modified = os.path.getmtime(stream.name)
        except os.error:
            pass
Response.cache_expires = cache_expires
# Utilisation de réponses conditionnées par défaut.
Response.default_conditional_response = True


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

        # Permet d'initialiser correctement la base de données.
        self.auth_backend = 'sqlalchemy'
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
        self.version = get_distribution("vigilo-%s" %
                                        self.app_name.lower()).version

        # Fournisseur de variables pour les templates.
        self.variable_provider = self._variable_provider

    def _variable_provider(self):
        """
        Fournisseur de variables pour les templates.
        Cette fonction est appelée à chaque fois qu'un template doit
        être affiché. Le dictionnaire retourné par cette fonction est
        fusionné avec les variables passées au template.

        @return: Dictionnaire de variables supplémentaires qui seront
            utilisables dans le template.
        @rtype: C{dict}
        """
        return {
            'asbool': asbool,
        }

    def setup_paths(self):
        """
        Surcharge pour modifier la liste des dossiers dans lesquels Genshi
        va chercher les templates, afin de supporter un système de thèmes.
                                                    """
        super(VigiloAppConfig, self).setup_paths()

        app_templates = resource_filename(
            'vigilo.themes.templates', self.app_name.lower())
        common_templates = resource_filename(
            'vigilo.themes.templates', 'common')

        self.paths['templates'] = [app_templates, common_templates]

        # Spécifique projets
        for module in ["turbogears", self.app_name.lower()]:
            for entry in working_set.iter_entry_points(
                                    "vigilo.%s.templates" % module):
                if (entry.name != "enterprise" and
                        entry.name not in self.get("extensions", [])):
                    # les points d'entrée "enterprise" sont automatiquement
                    # chargés, il faut lister les autres dans la conf
                    continue
                self.paths['templates'].insert(0, resource_filename(
                                           entry.module_name, "templates"))


    def setup_genshi_renderer(self):
        """
        Surcharge pour utiliser un traducteur personnalisé dans les
        modèles (templates).
        """
        def template_loaded(template):
            """Appelé lorsqu'un modèle finit son chargement."""
            import pylons
            # L'API pour Genshi a changé avec la version 0.6:
            # désormais, l'instance de traduction complète doit
            # être passée lors de la création du Translator.
            if parse_version(genshi_version) >= parse_version('0.6a1'):
                template.filters.insert(0, Translator(pylons.c.l_))
            else:
                template.filters.insert(0, Translator(pylons.c.l_.ugettext))

        def my_render_genshi(template_name, template_vars, **kwargs):
            """Ajoute une fonction l_ dans les modèles pour les traductions."""
            import pylons
            template_vars['l_'] = pylons.c.l_.ugettext
            return render_genshi(template_name, template_vars, **kwargs)

        loader = TemplateLoader(search_path=self.paths.templates,
                                auto_reload=self.auto_reload_templates,
                                callback=template_loaded,
                                max_cache_size=0)

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

        engine = configure_db(pylons_config, 'sqlalchemy.')
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

    def add_core_middleware(self, app):
        """
        Ajoute les middlewares vitaux au fonctionnement de l'application.

        Les middlewares relatifs à Beaker (cache et session) ne sont pas
        instanciés à cet endroit car on veut les rendre accessibles depuis
        le middleware d'authentification (repoze.who); ils doivent donc
        apparaître APRÈS dans la pile.

        Voir L{add_auth_middleware} pour savoir comment les middlewares
        de Beaker sont ajoutés.
        """
        app = RoutesMiddleware(app, config['routes.map'])
        return app

    def add_auth_middleware(self, app, skip_authentication):
        """
        Ajoute le middleware d'authentification.

        Contrairement à la méthode héritée de TurboGears, celle-ci
        ajoute en plus les middlewares de Beaker (session/cache).
        Voir L{add_core_middleware} pour plus d'information.
        """
        # Ajout du middleware d'authentification adapté pour Vigilo.
        auth_config = config.get('auth.config')
        if auth_config:
            app = make_middleware_with_config(
                app, config,
                auth_config,
                None,
                None,
                skip_authentication,
            )
            # On force l'utilisation d'un logger nommé "auth"
            # pour repoze.who (compatibilité avec TurboGears).
            app.logger = getLogger('auth')

        # On ajoute les middlewares de gestion de cache/sessions.
        # Normalement, add_core_middleware le fait, mais on veut
        # que ces middlewares soient utilisable depuis repoze.who,
        # donc on doit les ajouter APRÈS le middleware d'auth.
        app = SessionMiddleware(app, config)
        app = CacheMiddleware(app, config)
        return app

    def add_tosca_middleware(self, app):
        """
        Ajoute le middleware qui gère les ressources ToscaWidgets.

        La méthode est surchargée afin d'injecter dynamiquement
        dans la requête HTTP la configuration permettant la mise
        en cache (pour une durée de 1h) des ressources statiques
        de ToscaWidgets par le navigateur.

        @param app: Application WSGI à laquelle on ajoute la
            surcouche ToscaWidgets.
        @return: Une nouvelle application WSGI avec la surcouche
            ToscaWidgets.
        """
        wrapped_app = super(VigiloAppConfig, self).add_tosca_middleware(app)
        def _wrapper(environ, start_response):
            environ['toscawidgets.resources_expire'] = 3600
            return wrapped_app(environ, start_response)
        return _wrapper

    def init_config(self, global_conf, app_conf):
        """
        Dans Pylons 0.10, la pile WSGI n'est plus initialisée
        pour permettre l'utilisation du rendu Mako par défaut.
        De ce fait, les modules de rendu Buffet ne sont pas
        initialisés et l'affichage de contenu les nécessitant
        (ex: requêtes JSON) échoue.
        On force l'initialisation comme si on utilisait Mako
        pour toutes ces raisons.
        """
        super(VigiloAppConfig, self).init_config(global_conf, app_conf)
        pylons_config.set_defaults('mako')
