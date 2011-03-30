# -*- coding: utf-8 -*-
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
