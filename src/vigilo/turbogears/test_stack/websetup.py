# -*- coding: utf-8 -*-
# Copyright (C) 2017-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

__all__ = ['setup_app']

def setup_app(command, conf, variables):
    """Commandes d'initialisation de vigilo.turbogears"""
    from tg import config
    from vigilo.models.websetup import populate_db

    # La connexion à la base de données a déjà été créée
    # implicitement par la classe TestController et il ne faut pas
    # en recréer une nouvelle (car la base est stockée en RAM).
    # On se contente de peupler la base via la connexion existante.
    engine = config['tg.app_globals'].sa_engine
    populate_db(engine)
