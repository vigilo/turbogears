# -*- coding: utf-8 -*-
# Copyright (C) 2017 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from tg.i18n import lazy_ugettext as l_, ugettext as _
from sprox.widgets import TextField, PropertySingleSelectField, Label
from sqlalchemy import func
from formencode.api import FancyValidator, Invalid

from vigilo.models.session import DBSession
from vigilo.models import tables
from vigilo.models.tables.group import Group


class AccessField(PropertySingleSelectField):
    def _my_update_params(self, d, nullable=False):
        d.options = [('r', _('Read-only')), ('w', _('Read/write'))]
        return d


class ReadOnlyAccessField(Label):
    def update_params(self, d):
        super(ReadOnlyAccessField, self).update_params(d)
        accesses = {u'r': _('Read-only'), u'w': _('Read/write')}
        d.text = accesses[d.value['access']]
        return d


class GroupValidator(FancyValidator):
    """"""

    messages = dict(
        invalidId='Invalid identifier',
        invalidType='Invalid group type',
    )

    mapgroups = False
    supitemgroups = False
    graphgroups = False

    __unpackargs__ = ('mapgroups', 'supitemgroups', 'graphgroups')

    def _convert_to_python(self, value, state):
        try:
            idgroup = int(value)
        except (ValueError, TypeError):
            raise Invalid(self.message('invalidId', state), value, state)

        group = DBSession.query(Group).get(idgroup)
        if group is None:
            raise Invalid(self.message('invalidId', state), value, state)

        if isinstance(group, tables.MapGroup) and not self.mapgroups:
            raise Invalid(self.message('invalidType', state), value, state)
        if isinstance(group, tables.GraphGroup) and not self.graphgroups:
            raise Invalid(self.message('invalidType', state), value, state)
        if isinstance(group, tables.SupItemGroup) and not self.supitemgroups:
            raise Invalid(self.message('invalidType', state), value, state)
        return group

    def _convert_from_python(self, value, state):
        if not isinstance(value, Group):
            raise Invalid(self.message('invalidType', state), value, state)
        return unicode(value.idgroup)


class GroupField(PropertySingleSelectField):
    params = ["supitemgroups", "mapgroups", "graphgroups"]
    supitemgroups = False
    mapgroups = False
    graphgroups = False

    def __init__(self, id=None, parent=None, children=[], **kw):
        super(GroupField, self).__init__(id, parent, children, **kw)
        self.validator = GroupValidator(
            supitemgroups=self.supitemgroups,
            mapgroups=self.mapgroups,
            graphgroups=self.graphgroups,
        )

    def _my_update_params(self, d, nullable=False):
        options = []

        if nullable:
            options.append([None, "-----------"])

        groups = DBSession.query(
                Group
            ).join(
                (tables.GroupPath, Group.idgroup == tables.GroupPath.idgroup),
            ).order_by(Group.grouptype, func.lower(tables.GroupPath.path))

        by_group = {'MapGroup': [], 'SupItemGroup': [], 'GraphGroup': []}
        for group in groups:
            by_group[group.__class__.__name__].append( (group.idgroup, group.path) )

        if self.supitemgroups and by_group['SupItemGroup']:
            options.append( (l_("Monitoring groups"), by_group['SupItemGroup']) )

        if self.mapgroups and by_group['MapGroup']:
            options.append( (l_("Map groups"), by_group['MapGroup']) )

        if self.graphgroups and by_group['GraphGroup']:
            options.append( (l_("Graph groups"), by_group['GraphGroup']) )

        if len(options) == 0:
            return {}
        d['options']= options
        return d

