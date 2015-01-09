# -*- coding: utf-8 -*-
# Copyright (C) 2006-2015 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Un widget capable de gérer une énumération.
"""

import string
from tw import forms
from tw.rum.viewfactory import WidgetFactory, input_actions, inline_actions
from tw.rum import widgets, util
from rum import ViewFactory
from rum.fields import *
from rum.util import NoDefault
from tw.api import JSLink, JSSource, CSSLink
from tg import url
from tw.forms import validators
get = ViewFactory.get.im_func

class Enum(Field):
    """
    Ce champ permet de choisir une valeur parmi un ensemble limité
    de possibilités.
    """
    def __init__(self, name, options, required=False, label=None,
        default=NoDefault, read_only=False, searchable=True, sortable=True):
        super(Enum, self).__init__(name, required, label, default, read_only,
                                    searchable=searchable, sortable=sortable)
        if not isinstance(options, (list, tuple)):
            raise TypeError, options
        self.options = options

class EnumDisplay(widgets.Span):
    def update_params(self, d):
        super(EnumDisplay, self).update_params(d)
        options = dict(d.field.options)
        d.escape = False
        template = u'<span class="rum-field-value" title="%s">%s</span>'
        d.unicode_value = template % (options[d.unicode_value], d.unicode_value)


@get.before("isinstance(attr, Enum)")
def _set_options_for_enum(self, resource, parent, remote_name,
                                attr, action, args):
    args['options'] = attr.options
    v = validators.OneOf([o[0] for o in attr.options])
    self.add_validator(v, args)

@get.when("isinstance(attr, Enum) and action in inline_actions")
def _show_enum_tooltip(self, resource, parent, remote_name, attr, action, args):
    args['field'] = attr
    return EnumDisplay

WidgetFactory.register_widget(
    forms.SingleSelectField, Enum, input_actions, _prio=-1,
)
