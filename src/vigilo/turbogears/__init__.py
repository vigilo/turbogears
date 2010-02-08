# -*- coding: utf-8 -*-
"""
Contient les éléments de configuration pour Turbogears
communs à plusieurs applications de Vigilo.
"""

__all__ = ['populate_db', 'VigiloAppConfig']

from tg import config
from vigilo.turbogears.app_cfg import VigiloAppConfig

def populate_db():
    from vigilo.models import websetup

    # Cette méthode se contente d'appeler le websetup du modèle
    # en réutilisant la configuration de l'application stockée
    # dans la configuration de pylons.
    return websetup.populate_db(config['pylons.app_globals'].sa_engine)

