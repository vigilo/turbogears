# -*- coding: utf-8 -*-
# Copyright (C) 2011-2013 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce fichier contient les traductions que les modules
pour repoze.who/repoze.what doivent utiliser pour
interroger la base de données.
"""

from repoze.what.plugins.quickstart import find_plugin_translations

translations = find_plugin_translations({
    'groups': 'usergroups',
})
