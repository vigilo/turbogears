# -*- coding: utf-8 -*-
# Copyright (C) 2011-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce module contient un contrôleur pour TurboGears qui centralise
la gestion des méthodes relatives à l'auto-supervision.

Les applications feront généralement hériter leur contrôleur
principal de celui-ci.
"""

import logging
from datetime import datetime, timedelta
from tg.i18n import ugettext as _
from tg import expose, flash, config, request
from tg.predicates import Any, All, has_permission, not_anonymous
from vigilo.turbogears.controllers import BaseController
from vigilo.models.session import DBSession
from vigilo.models.tables import Host, LowLevelService, State, StateName

LOGGER = logging.getLogger(__name__)

class SelfMonitoringController(BaseController):
    """ Contrôleur centralisant les méthodes liées à l'auto-supervision """

    @expose('json')
    def get_failures(self):
        """
        Retourne la liste (au format JSON) des collecteurs Vigilo en panne.
        Déclenche un appel à la méthode flash si cette liste est non vide.
        """

        # On vérifie que l'utilisateurs dispose des permissions appropriées
        All(
            not_anonymous(msg=_("You need to be authenticated")),
            Any(
                config.is_manager,
                has_permission('%s-access' % config.app_name.lower()),
                msg=_("You don't have access to %s") % config.app_name
            )
        ).check_authorization(request.environ)

        # On récupère la liste des connecteurs en panne
        failures = self.check_connectors_freshness()

        # Si cette liste n'est pas vide, on affiche un message à l'utilisateur
        if failures:
            flash(_(
                    'Vigilo has detected a breakdown on the following '
                    'collector(s): %(list)s'
                  ) % {'list': ', '.join(failures)},
                  'error'
            )

        # Dans les 2 cas (liste vide ou non), on la retourne au format JSON
        return dict(failures=failures)

    def check_connectors_freshness(self):
        """
        Vérifie dans la base de données la date de dernière mise à jour de
        l'état des connecteurs Nagios. Retourne la liste des machines dont le
        connecteur Nagios n'a pas donné signe de vie depuis plus d'une certaine
        durée (modifiable dans le fichier de settings de l'application).
        """

        threshold = int(config['freshness_threshold'])
        if threshold <= 0:
            return []

        # On récupère dans la BDD la liste des connecteurs nagios
        # avec leur état et leur date de dernière mise à jour
        collectors = DBSession.query(
            Host.name,
            State.state,
            State.timestamp
        ).join(
            (LowLevelService, Host.idhost == LowLevelService.idhost)
        ).join(
            (State, LowLevelService.idservice == State.idsupitem)
        ).filter(
            LowLevelService.servicename == 'vigilo-connector-nagios'
        ).all()

        # En partant de cette première liste on en construit une
        # seconde ne contenant que les noms des connecteurs en panne
        collectors_down = []
        for c in collectors :
            if c.state not in [
                StateName.statename_to_value('OK'),
                StateName.statename_to_value('WARNING')
            ] or c.timestamp <= datetime.now() - timedelta(seconds=threshold):
                collectors_down.append(c.name)

        # On retourne cette seconde liste
        return collectors_down


