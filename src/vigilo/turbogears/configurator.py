# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import codecs
import pytz

from logging import getLogger
from pkg_resources import resource_filename, working_set, get_distribution
from tg import lurl
from tg.configuration.utils import TGConfigError
from tg.configurator.base import ConfigurationComponent, BeforeConfigConfigurationAction
from tg.configurator.minimal import MinimalApplicationConfigurator
from tg.configurator.components.auth import SimpleAuthenticationConfigurationComponent
from tg.configurator.components.debugger import DebuggerConfigurationComponent
from tg.configurator.components.error_pages import ErrorPagesConfigurationComponent
from tg.configurator.components.i18n import I18NConfigurationComponent
from tg.configurator.components.mimetypes import MimeTypesConfigurationComponent
from tg.configurator.components.seekable_request import SeekableRequestConfigurationComponent
from tg.configurator.components.session import SessionConfigurationComponent
from tg.configurator.components.sqlalchemy import SQLAlchemyConfigurationComponent
from tg.configurator.components.toscawidgets2 import ToscaWidgets2ConfigurationComponent
from tg.configurator.components.transactions import TransactionManagerConfigurationComponent
from tg.predicates import in_any_group
from tg.support.converters import asbool

from vigilo.turbogears.js_codec import backslash_search
from vigilo.turbogears.repoze.middleware import make_middleware_with_config

class VigiloConfigurationComponent(ConfigurationComponent):
    """
    A component that updates the templates' paths with additional paths
    related to the currently-loaded theme, application and extensions.

    It also configures the secret key used by Beaker to sign session cookies.
    """
    id = 'vigilo'

    def get_actions(self):
        return [BeforeConfigConfigurationAction(self._configure)]

    def _configure(self, conf, app):
        # Configure the secret key used by Beaker to sign session cookies.
        if 'secret' not in conf:
            raise TGConfigError("You must define a 'secret' value in your configuration")
        conf['session.secret'] = conf['secret']

        # Now configure lookup paths for templates.
        app_name = conf['app_name'].lower().replace('-', '_')
        tpl_paths = conf.setdefault('paths', {}).setdefault('templates', [])

        # Add the path to the current application's templates
        # and to the shared templates.
        tpl_paths += [
            resource_filename('vigilo.themes.templates', app_name),
            resource_filename('vigilo.themes.templates', 'common'),
        ]

        # Add the paths to the extensions' templates
        extensions = conf.get('extensions', [])
        for module in ["turbogears", app_name]:
            for entry in working_set.iter_entry_points("vigilo.%s.templates" % module):
                if (entry.name != "enterprise" and entry.name not in extensions):
                    # Les points d'entrée "enterprise" sont automatiquement
                    # chargés, il faut lister les autres dans la conf
                    continue
                tpl_paths.insert(0, resource_filename(entry.module_name, "templates"))

        conf['paths']['templates'] = tpl_paths


class VigiloSQLAlchemyConfigurationComponent(SQLAlchemyConfigurationComponent):
    """
    Extends SQLAlchemyConfigurationComponent to initialize Vigilo's model
    by default if no model is explicitly provided.
    """

    def setup_sqlalchemy(self, conf, app):
        # If an explicit model has been configured,
        # initialize it using TG's default component.
        if 'model' in conf:
            return super(VigiloSQLAlchemyConfigurationComponent, self).setup_sqlalchemy(conf, app)

        # Otherwise, initialize the model defined in vigilo.models.
        from vigilo.models.configure import configure_db
        engine = configure_db(conf, 'sqlalchemy.')
        conf['tg.app_globals'].sa_engine = engine

        # Keep track of the SQLA session.
        from vigilo.models import session
        conf['SQLASession'] = conf['DBSession'] = session.DBSession


class VigiloAuthenticationConfigurationComponent(SimpleAuthenticationConfigurationComponent):
    """
    Extends SimpleAuthenticationConfigurationComponent to use
    Vigilo's pre-configured repoze.who middleware instead of relying
    on TurboGears' default behaviour.
    """
    def _configure(self, conf, app):
        if 'secret' not in conf:
            raise TGConfigError("You must define a 'secret' value in your configuration")

        admin_groups = conf.get('admin_groups', 'managers').split(',')
        filtered_groups = filter(None, (s.strip() for s in admin_groups))
        conf['is_manager'] = in_any_group(*filtered_groups)

    def _add_middleware(self, conf, app):
        auth_conf = conf.get('auth.config')
        if auth_conf:
            app = make_middleware_with_config(
                app, conf,
                auth_conf,
                None,
                None,
                asbool(conf.get('skip_authentication', False)),
            )
            # On force l'utilisation d'un logger nommé "auth"
            # pour repoze.who (compatibilité avec TurboGears).
            app.logger = getLogger('auth')
        return app


class Configurator(MinimalApplicationConfigurator):
    def __init__(self, app_name, package):
        self._apply_monkey_patches()
        super(Configurator, self).__init__()

        self.update_blueprint({
            # Vigilo-specific settings
            'app_name': app_name,
            'version': get_distribution("vigilo-%s" % app_name.lower()).version,
            'variable_provider': self._variable_provider,

            # PathsConfigurationComponent and others
            'package': package,

            # DispatchConfigurationComponent
            'disable_request_extensions': False,
            'dispatch_path_translator': True,

            # ToscaWidgets2ConfigurationComponent
            'tw2.enabled': True,
            'custom_tw2_config': {'script_name': lurl('/')},

            # TemplateRenderingConfigurationComponent
            'use_dotted_templatenames': False,
            'renderers': ['genshi', 'mako', 'json'],
            'default_renderer': 'genshi',
            'templating.genshi.method': 'xhtml',

            # VigiloSQLAlchemyConfigurationComponent
            'use_sqlalchemy': True,

            # SessionConfigurationComponent
            'session.enabled': True,
            'session.type': 'file',   # Session storage backend (must be != 'cookie')
            'session.key': 'vigilo',  # Session cookie name
            'session.data_serializer': 'json',

            # MimeTypesConfigurationComponent
            'mimetype_lookup': {
                '.png':'image/png',
                '.csv': 'text/csv',
            },
        })

        # Used to inject application/extension-specific templates' paths.
        self.register(VigiloConfigurationComponent)

        self.register(I18NConfigurationComponent)
        self.register(VigiloAuthenticationConfigurationComponent)
        self.register(SessionConfigurationComponent)

        # from here on, due to TW2, the response is a generator
        # so any middleware that relies on the response to be
        # a string needs to be applied before this point.
        self.register(ToscaWidgets2ConfigurationComponent)

        self.register(VigiloSQLAlchemyConfigurationComponent)
        self.register(TransactionManagerConfigurationComponent)
        self.register(ErrorPagesConfigurationComponent)
        self.register(SeekableRequestConfigurationComponent)

        # Place the debuggers after the registry so that we
        # can preserve context in case of exceptions
        self.register(DebuggerConfigurationComponent, after=True)

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
            "asbool": asbool,
        }

    def _apply_monkey_patches(self):
        # Enregistre le codec pour l'encodage des textes dans le code JavaScript.
        codecs.register(backslash_search)
