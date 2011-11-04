# -*- coding: utf-8 -*-
"""
Ce fichier contient les traductions que les modules
pour repoze.who/repoze.what doivent utiliser pour
interroger la base de données.
"""

from repoze.what.plugins.quickstart import find_plugin_translations

translations = find_plugin_translations({
    'groups': 'usergroups',
})
