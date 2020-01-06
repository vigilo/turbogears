# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Definit la classe chargée de gérer la configuration des applications
utilisant Turbogears sur Vigilo.
"""
from __future__ import absolute_import

import codecs
from pkg_resources import resource_filename, working_set, get_distribution
from paste.deploy.converters import asbool
from logging import getLogger

from tg.configuration import AppConfig, config
from tg.configuration.app_config import config as tg_config
from tg.util import Bunch
from tg.predicates import in_any_group
from tw.core.resources import _JavascriptFileIter

from vigilo.turbogears.js_codec import backslash_search

# Middleware d'authentification adapté à nos besoins.
from vigilo.turbogears.repoze.middleware import make_middleware_with_config

# Enregistre le codec pour l'encodage des textes dans le code JavaScript.
codecs.register(backslash_search)

__all__ = ('VigiloAppConfig', )

class VigiloAppConfig(AppConfig):
    """On modifie AppConfig selon nos besoins."""

    def __init__(self, app_name):
        """Crée une nouvelle configuration."""
        super(VigiloAppConfig, self).__init__()
        self.app_name = app_name
        self.use_toscawidgets = True
        self.use_toscawidgets2 = False
        self.is_manager = None

        # On désactive la recherche de template basée sur les modules Python.
        # Ceci évite que TurboGears ne s'y perde lorsqu'on demande à charger
        # un template non-HTML comme "get_all.xml".
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

        # La méthode translate() sur un objet de type unicode n'accepte
        # que des caractères unicode en guise de mapping et le chemin
        # de la requête est en unicode dans les versions récentes de WebOb.
        _JavascriptFileIter.TRANSLATION_TABLE = \
            unicode(_JavascriptFileIter.TRANSLATION_TABLE)

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

    def _setup_package_paths(self):
        """
        Surcharge pour modifier la liste des dossiers dans lesquels Genshi
        va chercher les templates, afin de supporter un système de thèmes.
                                                    """
        super(VigiloAppConfig, self)._setup_package_paths()

        app_templates = resource_filename(
            'vigilo.themes.templates', self.app_name.lower().replace('-', '_'))
        common_templates = resource_filename(
            'vigilo.themes.templates', 'common')

        self.paths['templates'] += [app_templates, common_templates]

        # Spécifique projets
        for module in ["turbogears", self.app_name.lower().replace('-', '_')]:
            for entry in working_set.iter_entry_points(
                                    "vigilo.%s.templates" % module):
                if (entry.name != "enterprise" and
                        entry.name not in self.get("extensions", [])):
                    # les points d'entrée "enterprise" sont automatiquement
                    # chargés, il faut lister les autres dans la conf
                    continue
                self.paths['templates'].insert(0, resource_filename(
                                           entry.module_name, "templates"))

    def setup_sqlalchemy(self):
        """
        Turbogears a besoin de configurer la session de base de données.
        Puis normalement, il appelle la fonction init_model() du modèle
        de l'application avec les paramètres de la session.
        Dans notre cas, la session est déjà configurée globalement (dans
        vigilo.models.session), donc cette étape n'est pas nécessaire.
        On inhibe le comportement de Turbogears ici.
        """
        from vigilo.models.configure import configure_db

        engine = configure_db(tg_config, 'sqlalchemy.')
        config['tg.app_globals'].sa_engine = engine

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
        self.sa_auth.translations = Bunch()
        self.sa_auth.translations.groups = 'usergroups'

    def add_auth_middleware(self, app, skip_authentication):
        """
        Ajoute le middleware d'authentification.
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
        return app

    def after_init_config(self):
        """
        Initialisation du prédicat permettant de vérifier l'appartenance
        aux groupes des administrateurs.
        """
        admin_groups = tg_config.get('admin_groups', 'managers')
        if admin_groups.strip():
            groups_list = [s.strip() for s in admin_groups.split(',')]
        else:
            # Si la valeur dans le fichier de configuration
            # est vide (ou ne contient que des blancs),
            # alors il n'y a aucun groupe d'utilisateurs
            # privilégiés.
            groups_list = []

        # Cette affectation permet aux applications d'utiliser
        # le prédicat via `tg.config.is_manager`.
        # La liste est transformée en arguments pour la fonction,
        # ie. in_any_group(groups_list[0], groups_list[1], ...)
        config.is_manager = in_any_group(*groups_list)

        # Celle-ci permet aux tests unitaires de vigilo.turbogears
        # d'utiliser le prédicat elles-aussi.
        self.is_manager = config.is_manager

