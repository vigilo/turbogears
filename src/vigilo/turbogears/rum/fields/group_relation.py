# -*- coding: utf-8 -*-
# Copyright (C) 2006-2015 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Un widget capable de gérer une relation basée sur un groupe d'objets.
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

from pylons.i18n import ugettext as _
from vigilo.models.tables import SupItemGroup, MapGroup

class GroupSelector(forms.InputField):
    javascript = [
        # Frameworks dont le widget dépend.
        JSLink(link=url('/js/lib/mootools.js')),
        JSLink(link=url('/js/lib/mootools-more.js')),
        JSLink(link=url('/js/lib/jxlib.js')),

        # Traductions.
        JSLink(link=url('/js/lib/babel.js')),
        JSLink(link=url('/js/lib/babelThemes.js')),
        JSLink(link=url('/i18n')),

        # Code JavaScript du widget à proprement parler.
        JSLink(link=url('/js/grouptree.js')),
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
    var container = new Element('div');
    container.setStyle("padding", "0 10px 10px 10px");

    var req = new Request.JSON({
        method: "get",
        noCache: true,
        link: "chain",
        url: '${path_url}',
        onSuccess: function (data) {
            $('${id}.ui').set('value', data.path);
        }
    });

    var dlg = new Jx.Dialog({
        label: '',
        modal: true,
        content: container
    });

    var tree = new GroupTree({
        parent: container,
        url: '${groups_url}',
        itemName: null,
        groupingItemName: null,
        groupsonly: true,
        imgpath: '${app_url}',
        onGroupClick: function (item) {
            $('${id}.value').set('value', item.id);
            req.send({data: {idgroup: item.id}});
            dlg.close();
        }
    });

    $('${id}').store('dlg', dlg);
    $('${id}').store('tree', tree);

    $('${id}').addEvent('click', function () {
        var dlg = this.retrieve('dlg');
        var tree = this.retrieve('tree');
        if (!tree.isLoaded) {
            tree.load();
        }
        dlg.open();
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
            if d.field.single_type:
                # S'il n'y a qu'un seul type de groupes à représenter,
                # inutile d'afficher un préfixe spécifique.
                d.text_value = d.value.path
            elif isinstance(d.value, SupItemGroup):
                d.text_value = u'/' + _('Groups of monitored items') + \
                                d.value.path
            elif isinstance(d.value, MapGroup):
                d.text_value = u'/' + _('Groups of maps') + \
                                d.value.path[5:]
            d.value = str(d.value.idgroup)
        d.groups_url = d.field.groups_url
        d.path_url = d.field.path_url
        d.app_url = url('/images');

class GroupRelation(Relation):
    def __init__(self, groups_url, path_url, single_type=False,
                *args, **kwargs):
        super(GroupRelation, self).__init__(*args, **kwargs)
        self.groups_url = groups_url
        self.path_url = path_url
        self.single_type = single_type

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

WidgetFactory.register_widget(
    GroupSelector, GroupRelation, input_actions, _prio=10,
)
