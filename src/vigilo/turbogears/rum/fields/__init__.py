# -*- coding: utf-8 -*-
# Copyright (C) 2011-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Champs spécifiques rum pour Vigilo."""

__all__ = (
    'Enum',
    'CitedRelation',
    'GroupRelation',
)

# Importés pour centraliser la gestion des champs.
from rum.fields import *

from .enum import Enum
from .cited_relation import CitedRelation
from .group_relation import GroupRelation
