# -*- coding: utf-8 -*-
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Contient les éléments de configuration pour Turbogears
communs à plusieurs applications de Vigilo.
"""

__all__ = ['populate_db', 'VigiloAppConfig']

from tg import config
from vigilo.turbogears.app_cfg import VigiloAppConfig

def populate_db():
    """
    Configure la base de données et l'initialise.
    L'initialisation de la base de données crée les tables et insère
    les données nécessaires pour commencer à utiliser Vigilo.
    """
    from vigilo.models.configure import configure_db
    engine = configure_db(config, 'sqlalchemy.')

    # Cette méthode se contente d'appeler le websetup du modèle
    # en réutilisant la configuration de l'application stockée
    # dans la configuration de pylons.
    from vigilo.models import websetup
    return websetup.populate_db(engine)
