# -*- coding: utf-8 -*-

from tw import forms
from tw.rum.viewfactory import WidgetFactory, input_actions, inline_actions
from tw.rum import widgets
from rum import ViewFactory
from rum.fields import Field, Relation
from rum.util import NoDefault
from tw.forms import validators

get = ViewFactory.get.im_func

class Enum(Field):
    def __init__(self, name, options, required=False, label=None,
        default=NoDefault, read_only=False, searchable=True, sortable=True):
        super(Enum, self).__init__(name, required, label, default, read_only,
                                    searchable=searchable, sortable=sortable)
        if not isinstance(options, dict):
            raise TypeError, options

        self.options = options
class CitedRelation(Relation):
    pass


@get.before("isinstance(attr, Enum)")
def _set_options_for_enum(self, resource, parent, remote_name,
                                attr, action, args):
    def get_options():
        options = list(attr.options.iteritems())
        return options

    options = get_options()
    args['options'] = options
    v = validators.OneOf([o[0] for o in options])
    self.add_validator(v, args)

@get.around("isinstance(attr, CitedRelation) and action in inline_actions", prio=10)
def _widget_for_cited_relation(self, resource, parent, remote_name, attr, action, args):
    args['field'] = attr
    return widgets.ExpandableSpan

WidgetFactory.register_widget(
    forms.SingleSelectField, Enum, input_actions, _prio=-1,
)

WidgetFactory.register_widget(
    forms.SingleSelectField, CitedRelation, input_actions, _prio=10,
)

