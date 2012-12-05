# -*- coding: utf-8 -*-
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce module contient un contrôleur pour TurboGears qui facilite
l'intégration de personnalisations.

Les applications inclueront généralement une instance de ce contrôleur
dans leur C{RootController}. Le contrôleur charge ensuite automatiquement
des sous-contrôleurs, à partir d'un point d'entrée "<application>.controllers".
"""

import re
import logging
from pkg_resources import working_set
from tg import config
from pylons.i18n import ugettext as _
from vigilo.turbogears.controllers import BaseController

LOGGER = logging.getLogger(__name__)

class CustomController(BaseController):
    """
    Un contrôleur qui facilite l'ajout d'extensions / personnalisations
    par des développeurs tiers.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise le contrôleur en lui ajoutant dynamiquement
        des attributs (sous-contrôleurs), en fonction des points
        d'entrée définis dans le groupe "<application>.controllers".
        """
        app_name = str(config.get('app_name')).lower()
        group = '%s.controllers' % app_name
        LOGGER.debug("Loading custom controllers")
        for ep in working_set.iter_entry_points(group):
            if not re.match('^[a-z][a-z0-9_]*$', ep.name, re.I):
                LOGGER.warning(_("Not a valid controller name: %s"), ep.name)
            else:
                ctrl = ep.load()
                if issubclass(ctrl, BaseController):
                    LOGGER.debug("Added custom controller '%s'" % ep.name)
                    setattr(self, ep.name, ctrl())
                else:
                    base_ctrl = "%s.%s" % (BaseController.__module__,
                                           BaseController.__name__)
                    ep_path = "%s.%s" % (ep.module_name, ep.attrs[0])
                    LOGGER.warning(
                        _("%(entry)s is not a subclass of %(base)s"),
                        {
                            'base': base_ctrl,
                            'entry': ep_path,
                        })
        super(CustomController, self).__init__(*args, **kwargs)
