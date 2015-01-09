# -*- coding: utf-8 -*-
# Copyright (C) 2011-2015 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Version personnalisée du contrôleur de Rum."""

from tgrum import RumAlchemyController, TGDummyPolicy
from vigilo.models import session
from vigilo.turbogears.rum.configuration import get_rum_config

__all__ = ('RumController', 'RumControllerModel')

class RumController(RumAlchemyController, object):
    """
    Wrapper pour le contrôleur de Rum.
    On se contente d'enregistrer des traductions pour les noms des
    classes du modèle.
    """
    def __init__(self, models, allow_only=None, template_path=None,
                    render_flash=True, policy=TGDummyPolicy):

        config = get_rum_config(models)
        super(RumController, self).__init__(session, allow_only,
                template_path, config, render_flash, policy)

