# -*- coding: utf-8 -*-
"""
Module fournissant des types de champs additionnels pour rum.
"""

import string
from tw import forms
from tw.rum.viewfactory import WidgetFactory, input_actions, inline_actions
from tw.rum import widgets, util
from rum import ViewFactory
from rum.fields import Field, Relation
from rum.util import NoDefault
from tw.api import JSLink, JSSource, CSSLink
from tg import url
from tw.forms import validators
get = ViewFactory.get.im_func

from pylons.i18n import ugettext as _
from vigilo.models.tables import SupItemGroup

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

class CitedRelation(Relation):
    """
    Ce champ fonctionne exactement comme le type C{Relation} de rum.fields,
    sauf qu'il ne fournit pas de liens entre les entités.
    Utilisez ce champ lorsque vous souhaitez pouvoir lier l'objet à d'autres
    sans que les objets pointés soient accessibles directement (modifiables).
    """
    pass

class GroupSelector(forms.InputField):
    javascript = [
        JSLink(link=url('/js/lib/mootools.js')),
        JSLink(link=url('/js/lib/mootools-more.js')),
        JSLink(link=url('/js/lib/jxlib.js')),
        JSLink(link=url('/js/tree.js')),
    ]
    css = [
        CSSLink(link=url('/css/jxlib/jxtheme.uncompressed.css')),
    ]
    params = ["choose_text", "text_value", "clear_text", "groups_url", "field"]
    choose_text = 'Choose'
    clear_text = 'Clear'
    text_value = ''
    groups_url = None

    template = """
<div xmlns="http://www.w3.org/1999/xhtml"
   xmlns:py="http://genshi.edgewall.org/" py:strip="">
<input type="hidden" name="${name}" class="${css_class}"
    id="${id}.value" value="${value}" />
<input type="text" class="${css_class}" id="${id}.ui"
    value="${text_value}" readonly="readonly" />
<input type="button" class="${css_class}" id="${id}" value="${choose_text}" />
<input type="button" class="${css_class}" id="${id}.clear" value="${clear_text}" />
<script type="text/javascript">
window.addEvent('load', function () {
    $('${id}').store('tree', new TreeGroup({
        title: '',
        url: '${groups_url}',
    }));
    $('${id}').addEvent('click', function () {
        var tg = this.retrieve('tree');
        tg.selectGroup();
        tg.addEvent('select', function (item) {
            var node = item;
            var label = '';
            for (; node.owner; node = node.owner) {
                label = '/' + node.options.label + label;
            }
            $('${id}.ui').set('value', label);
            $('${id}.value').set('value', item.options.data);
        });
    }.bind($('${id}')));

    $('${id}.clear').addEvent('click', function () {
        $('${id}.ui').set('value', '');
        $('${id}.value').set('value', '');
    });
});
</script>
</div>
"""

    def update_params(self, d):
        from vigilo.models.session import DBSession
        from vigilo.models.tables.group import Group
        super(GroupSelector, self).update_params(d)
        if not d.value:
            d.text_value = ''
            d.value = ''
        else:
            if isinstance(d.value, SupItemGroup):
                d.text_value = u'/' + _('Groups of monitored items') + \
                                d.value.path
            else:
                # Sinon, c'est un MapGroup.
                # On masque le préfixe "/Root".
                d.text_value = u'/' + _('Groups of maps') + \
                                d.value.path[5:]
            d.value = str(d.value.idgroup)
        d.groups_url = d.field.groups_url

class GroupRelation(Relation):
    def __init__(self, groups_url, *args, **kwargs):
        super(GroupRelation, self).__init__(*args, **kwargs)
        self.groups_url = groups_url

class GroupLink(widgets.Span):
    def update_params(self, d):
        super(GroupLink, self).update_params(d)
        if d.value is None:
            d.unicode_value = u''
        elif isinstance(d.value, SupItemGroup):
            d.unicode_value = u'/' + _('Groups of monitored items') + \
                                d.value.path
        else:
            # Sinon, c'est un MapGroup.
            # On masque le préfixe "/Root".
            d.unicode_value = u'/' + _('Groups of maps') + \
                                d.value.path[5:]

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

@get.around("isinstance(attr, CitedRelation) and "
            "action in inline_actions", prio = 10)
def _widget_for_cited_relation(self, resource, parent, remote_name,
                                attr, action, args):
    """
    Modifie la vue pour éviter que des liens d'édition/consultation
    vers la cible de la relation ne soient ajoutés.
    """
    args['field'] = attr
    return widgets.ExpandableSpan

@get.when("isinstance(attr, GroupRelation) and "
            "action in inline_actions", prio = 10)
def _widget_for_group_relation(self, resource, parent, remote_name,
                                attr, action, args):
    args['field'] = attr
    return GroupLink

@get.before("isinstance(attr, GroupRelation)", prio = 10)
def _url_for_group_relation(self, resource, parent, remote_name,
                                attr, action, args):
    args['field'] = attr


# Enregistrement des champs personalisés auprès de rum.
WidgetFactory.register_widget(
    forms.SingleSelectField, Enum, input_actions, _prio=-1,
)

WidgetFactory.register_widget(
    forms.SingleSelectField, CitedRelation, input_actions, _prio=10,
)

WidgetFactory.register_widget(
    GroupSelector, GroupRelation, input_actions, _prio=10,
)
