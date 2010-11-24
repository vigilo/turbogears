# -*- coding: utf-8 -*-
"""
Module fournissant des types de champs additionnels pour rum.
"""

import string
from tw import forms
from tw.rum.viewfactory import WidgetFactory, input_actions, inline_actions
from tw.rum import widgets
from rum import ViewFactory
from rum.fields import Field, Relation
from rum.util import NoDefault
from tw.forms import validators
from tw.api import JSLink, JSSource, CSSLink
from tg import url

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
        if not isinstance(options, dict):
            raise TypeError, options
        self.options = options

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
    params = ["choose_text", "text_value", "clear_text"]
    choose_text = 'Choose'
    clear_text = 'Clear'
    text_value = ''

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
    $('${id}').addEvent('click', function () {
        var tg = new TreeGroup({
            title: '',
            url: '%(url)s',
        });
        tg.selectGroup();
        tg.addEvent('select', function (item) {
            $('${id}.ui').set('value', item.options.label);
            $('${id}.value').set('value', item.options.data);
        });
    });

    $('${id}.clear').addEvent('click', function () {
        $('${id}.ui').set('value', '');
        $('${id}.value').set('value', '');
    });
});
</script>
</div>
""" % {
    'url': url('/get_groups'),
}

    def update_params(self, d):
        from vigilo.models.session import DBSession
        from vigilo.models.tables.group import Group
        super(GroupSelector, self).update_params(d)
        if not d.value:
            d.text_value = ''
            d.value = ''
        else:
            d.text_value = d.value.name
            d.value = str(d.value.idgroup)

class GroupRelation(Relation):
    pass

class GroupLink(widgets.RelationLink):
    template = widgets.Span.template

@get.before("isinstance(attr, Enum)")
def _set_options_for_enum(self, resource, parent, remote_name,
                                attr, action, args):
    """Passe les options de l'énumération à la vue."""
    def get_options():
        """Retourne les options de l'énumération."""
        options = list(attr.options.iteritems())
        return options

    options = get_options()
    args['options'] = options
    v = validators.OneOf([o[0] for o in options])
    self.add_validator(v, args)

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

