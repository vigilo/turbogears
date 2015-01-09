# -*- coding: utf-8 -*-
# Copyright (C) 2006-2015 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from rumalchemy.query import SAQuery, normalize
from rum import query as rumquery
from rumalchemy.util import get_mapper, get_dialect_name
from rum.genericfunctions import generic

__all__ = (
    'normalize',
    'VigiloQuery',
    'apply_default_ordering',
    'apply_sort',
    'apply_joins',
    'remap_sort_column',
    'set_query_options',
    'translate',
)

class VigiloQuery(SAQuery):
    def filter(self, query):
        assert self.resource

        if self.expr is not None:
            query = self._apply_expression(query)

        query = self.apply_joins(query)
        self.count = query.count()

        query = self.apply_sort(query)

        if self.limit is not None:
            query = self._apply_limit(query)

        if self.offset is not None:
            query = self._apply_offset(query)

        query = self.set_query_options(query)
        return query

    @generic
    def apply_joins(self, query):
        pass

    @apply_joins.when()
    def _apply_default_joins(self, query):
        return query

    @generic
    def apply_sort(self, query):
        pass

    @apply_sort.when()
    def _apply_default_ordering(self, query):
        return self.apply_default_ordering(query)

    @apply_sort.when("self.sort is not None")
    def _apply_ordering(self, query):
        return super(VigiloQuery, self)._apply_sort(query)

    def get_column(self, resource, column_name, query):
        if not isinstance(column_name, basestring):
            return column_name
        res = super(VigiloQuery, self).get_column(resource, column_name, query)
        if res is False:
            raise ValueError
        return res


rumquery.QueryFactory.register(VigiloQuery,
    pred="get_mapper(resource) is not None", _prio=100)

apply_default_ordering = VigiloQuery.apply_default_ordering.im_func
apply_sort = VigiloQuery.apply_sort.im_func
apply_joins = VigiloQuery.apply_joins.im_func
remap_sort_column = VigiloQuery.remap_sort_column.im_func
set_query_options = VigiloQuery.set_query_options.im_func
translate = VigiloQuery.translate.im_func

# Les conventions choisies par Rum pour la suppression des accents
# sont plutôt arbitraires (pas vraiment adaptées pour le français).
# On les adapte donc ici pour quelque chose de plus générique.
@normalize.when("get_dialect_name().lower().startswith('postgres')", prio=10)
def _lower_and_accents(s):
    from sqlalchemy.ext.associationproxy import AssociationProxy
    from sqlalchemy import sql

    # Pour les proxies, on doit utiliser l'attribut référencé.
    if isinstance(s, AssociationProxy):
        s = getattr(s.target_class, s.value_attr)

    lower = sql.func.lower
    translate = sql.func.translate
    replace = sql.func.replace
    return replace(translate(
            lower(s),
            u'äëïöüÿáéíóúàèìòùâêîôûç',
            u'aeiouyaeiouaeiouaeiouc'
        ), 'ß', 'ss')
