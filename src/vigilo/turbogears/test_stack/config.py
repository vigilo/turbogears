# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

__all__ = ['make_app']


def make_app(global_conf, **app_conf):
    from .app_cfg import base_config

    # Initialisation de l'application et de son environnement d'exécution.
    return base_config.make_wsgi_app(global_conf, app_conf, wrap_app=None)
