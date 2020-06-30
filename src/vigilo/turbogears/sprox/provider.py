# -*- coding: utf-8 -*-
# Copyright (C) 2017-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from sprox.sa.provider import SAORMProvider
from sprox.sa.support import PropertyLoader, resolve_entity
from sqlalchemy import func
from sqlalchemy.orm import Mapper
from warnings import warn

class ProviderSelector(object):
    def __init__(self):
        self.provider = None

    def get_provider(self, entity=None, hint=None, **hints):
        if self.provider is None:
            self.provider = DataProvider(hint, **hints)
        return self.provider

    def get_selector(self, entity=None, **hints):
        return self

class DataProvider(SAORMProvider):
    def get_dropdown_options(self, entity, field_name, view_names=None):
        """
        Code repris de Sprox, mais qui trie automatiquement les résultats.
        """
        if view_names is None:
            view_names = self.default_view_names

        if self.session is None:
            warn('No dropdown options will be shown for %s.  '
                 'Try passing the session into the initialization '
                 'of your form base object so that this sprocket '
                 'can have values in the drop downs'%entity)
            return []

        field = self.get_field(entity, field_name)

        target_field = entity
        if isinstance(field, PropertyLoader):
            target_field = field.argument
        target_field = resolve_entity(target_field)

        #some kind of relation
        if isinstance(target_field, Mapper):
            target_field = target_field.class_

        pk_fields = self.get_primary_fields(target_field)
        view_name = self.get_view_field_name(target_field, view_names)

        # Trie automatiquement les valeurs en fonction de leur label.
        rows = self.session.query(target_field).order_by(
            func.lower(getattr(target_field, view_name))).all()

        if len(pk_fields) == 1:
            def build_pk(row):
                return getattr(row, pk_fields[0])
        else:
            def build_pk(row):
                return "/".join([str(getattr(row, pk)) for pk in pk_fields])

        return [ (build_pk(row), getattr(row, view_name)) for row in rows ]

