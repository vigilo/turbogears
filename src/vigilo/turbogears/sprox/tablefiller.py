# -*- coding: utf-8 -*-
# Copyright (C) 2017-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from tgext.crud.utils import RequestLocalTableFiller

class TableFiller(RequestLocalTableFiller):
    def _do_get_provider_count_and_objs(self, **kw):
        """
        Code repris de Sprox, mais qui peuple aussi "field_names",
        afin de pouvoir récupérer correctement les valeurs des attributs
        des tables étrangères dans certaines situations.
        """
        limit = kw.pop('limit', None)
        offset = kw.pop('offset', None)
        order_by = kw.pop('order_by', None)
        desc = kw.pop('desc', False)
        substring_filters = kw.pop('substring_filters', [])
        count, objs = self.__provider__.query(self.__entity__, limit, offset, self.__limit_fields__,
                                              order_by, desc, substring_filters=substring_filters,
                                              filters=kw, search_related=True,
                                              field_names=self.__possible_field_names__,
                                              related_field_names=self.__possible_field_names__)
        self.__count__ = count
        return count, objs
