# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from tw2.core import Param
from tg.i18n import lazy_ugettext as l_, ugettext as _
from sprox.widgets import TextField, PropertySingleSelectField, Label
from sqlalchemy import func
from formencode.api import FancyValidator, Invalid

from vigilo.models.session import DBSession
from vigilo.models import tables
from vigilo.models.tables.group import Group


class AccessField(PropertySingleSelectField):
    def prepare(self):
        self.options = [(u'r', _('Read-only')), (u'w', _('Read/write'))]
        if not self.value:
            self.value = ''
        super(PropertySingleSelectField, self).prepare()



class ReadOnlyAccessField(Label):
    def prepare(self):
        super(ReadOnlyAccessField, self).prepare()
        accesses = {u'r': _('Read-only'), u'w': _('Read/write')}
        self.text = accesses[self.value['access']]


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
        group = DBSession.query(Group).get(value)
        if not group:
            raise Invalid(self.message('invalidId', state), value, state)
        return value


class GroupField(PropertySingleSelectField):
    supitemgroups = Param('supitemgroups', attribute=False, default=False)
    mapgroups = Param('mapgroups', attribute=False, default=False)
    graphgroups = Param('graphgroups', attribute=False, default=False)

    def __init__(self, **kw):
        super(GroupField, self).__init__(**kw)
        self.provider = None
        self.validator = GroupValidator(
            supitemgroups=self.supitemgroups,
            mapgroups=self.mapgroups,
            graphgroups=self.graphgroups,
        )

    def prepare(self):
        entity = self.__class__.entity

        options = []

        if self.nullable:
            options.append(['', "-----------"])

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

        self.options = options
        if not self.value:
            self.value = ''
        super(PropertySingleSelectField, self).prepare()
