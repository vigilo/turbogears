# -*- coding: utf-8 -*-
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Un widget qui affiche les objets appartenant à une relation,
mais sans créer de lien vers l'objet référencé.
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

class CitedRelation(Relation):
    """
    Ce champ fonctionne exactement comme le type C{Relation} de rum.fields,
    sauf qu'il ne fournit pas de liens entre les entités.
    Utilisez ce champ lorsque vous souhaitez pouvoir lier l'objet à d'autres
    sans que les objets pointés soient accessibles directement (modifiables).
    """
    pass

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

WidgetFactory.register_widget(
    forms.SingleSelectField, CitedRelation, input_actions, _prio=10,
)
