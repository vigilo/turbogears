# -*- coding: utf-8 -*-
# Copyright (C) 2017 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

__all__ = ['make_app']

def make_app(global_conf, full_stack=True, **app_conf):
    from .app_cfg import base_config

    load_environment = base_config.make_load_environment()
    make_base_app = base_config.setup_tg_wsgi_app(load_environment)
    return make_base_app(global_conf, full_stack=True, **app_conf)
