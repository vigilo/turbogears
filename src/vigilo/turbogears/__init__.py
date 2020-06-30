# -*- coding: utf-8 -*-
# Copyright (C) 2011-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Contient les éléments de configuration pour Turbogears
communs à plusieurs applications de Vigilo.
"""

import os
from paste.deploy import loadapp as deploy_loader
from ConfigParser import SafeConfigParser
from logging.config import fileConfig
from tg import config
from vigilo.turbogears.app_cfg import VigiloAppConfig

__all__ = ['populate_db', 'VigiloAppConfig', 'loadapp']

def populate_db():
    """
    Configure la base de données et l'initialise.
    L'initialisation de la base de données crée les tables et insère
    les données nécessaires pour commencer à utiliser Vigilo.
    """
    from vigilo.models.configure import configure_db
    engine = configure_db(config, 'sqlalchemy.')

    # Cette méthode se contente d'appeler le websetup du modèle
    # en réutilisant la configuration de l'application déjà chargée.
    from vigilo.models import websetup
    return websetup.populate_db(engine)

def loadapp(ini_file):
    """
    Cette fonction permet de charger une application WSGI
    depuis un fichier INI définissant celle-ci (via une
    section "app:main").

    Cette fonction retourne l'application ainsi chargée,
    et peut être appelée depuis le point d'entrée WSGI :

        from vigilo.turbogears import loadapp
        application = loadapp('/etc/.../settings.ini')
    """
    ini_file = os.path.join('/', *ini_file.split('/'))
    parser = SafeConfigParser()
    parser.read([ini_file])
    if parser.has_section('loggers'):
        config_file = os.path.abspath(ini_file)
        config_options = dict(
            __file__=config_file,
            here=os.path.dirname(config_file)
        )
        fileConfig(config_file, config_options,
                   disable_existing_loggers=False)
    return deploy_loader('config:%s' % ini_file)
