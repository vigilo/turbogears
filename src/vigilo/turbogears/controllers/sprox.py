# -*- coding: utf-8 -*-
# Copyright (C) 2017-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from tg import expose, tmpl_context
from tg.i18n import lazy_ugettext as l_, ugettext as _
from markupsafe import Markup
from tw.forms import SubmitButton
from tgext.crud import EasyCrudRestController

from vigilo.turbogears.sprox.provider import ProviderSelector
from vigilo.turbogears.sprox.tablefiller import TableFiller
from vigilo.turbogears.controllers import BaseController


__all__ = ['BaseSproxController']

class MarkupWrapper(object):
    def __init__(self, markup):
        self.markup = markup

    def __unicode__(self):
        return self.markup

class BaseSproxController(EasyCrudRestController, BaseController):
    title = l_('Administration')
    pagination = {"items_per_page": 25}
    provider_type_selector_type = ProviderSelector

    def _actions_links(self, obj):
        """Override this function to define how action links should be displayed for the given record."""
        primary_fields = self.provider.get_primary_fields(self.model)
        pklist = '/'.join(map(lambda x: str(getattr(obj, x)), primary_fields))
        html = u"""
<div><div>&nbsp;<a href="%(pklist)s/edit" style="text-decoration:none">%(edit_label)s</a>
      </div><div>
      <form method="POST" action="%(pklist)s" class="button-to">
    <input type="hidden" name="_method" value="DELETE" />
    <input class="delete-button" onclick="return confirm('%(confirm)s');" value="%(delete_label)s" type="submit"
        style="background-color: transparent; float:left; border:0; color: #286571; display: inline; margin: 0; padding: 0;"/>
</form>
</div></div>""" % {
            'pklist': pklist,
            'confirm': _('Are you sure?').replace('\\', '\\\\').replace("'", "\\'"),
            'edit_label': _('Edit'),
            'delete_label': _('Delete'),
        }
        # le Markup est transformé en chaîne Unicode par Sprox,
        # puis échappé par tw.forms (ce qui casse le code HTML).
        # On contourne le problème en ajoutant un wrapper intermédiaire.
        return MarkupWrapper(Markup(html))

    @expose('genshi:admin/get_all.html', inherit=True)
    def get_all(self, *args, **kw):
        # Permet de définir un champ de tri par défaut
        default_sort_field = getattr(self, 'default_sort', None)
        if 'order_by' not in kw and default_sort_field:
            kw['order_by'] = default_sort_field
        return super(BaseSproxController, self).get_all(*args, **kw)

    @expose('genshi:admin/get_one.html', inherit=True)
    def get_one(self, *args, **kw):
        return super(BaseSproxController, self).get_one(*args, **kw)

    @expose('genshi:admin/edit.html', inherit=True)
    def edit(self, *args, **kw):
        return super(BaseSproxController, self).edit(*args, **kw)

    @expose('genshi:admin/new.html', inherit=True)
    def new(self, *args, **kw):
        return super(BaseSproxController, self).new(*args, **kw)

    @expose('genshi:admin/get_delete.html', inherit=True)
    def get_delete(self, *args, **kw):
        return super(BaseSproxController, self).get_delete(*args, **kw)

    def _before(self, *args, **kw):
        tmpl_context.readonly = getattr(self, 'readonly', False)
        tmpl_context.model_label = getattr(self, 'model_label', self.model.__name__)
        BaseController._before(self, *args, **kw)
        EasyCrudRestController._before(self, *args, **kw)

    def __init__(self, session, menu_items=None):
        # Personnalise les liens associés aux actions (ajout de traductions).
        if not hasattr(self, '__table_options__'):
            self.__table_options__ = {}
        self.__table_options__['__actions__'] = self._actions_links

        # Personnalise le bouton "Submit" du formulaire (ajout de traduction).
        if not hasattr(self, '__form_options__'):
            self.__form_options__ = {}
        self.__form_options__.setdefault('__add_fields__', {})['submit'] = \
            SubmitButton('submit', default=l_('Submit'))

        # Personnalise le provider (et son sélecteur) afin que les valeurs
        # des listes déroulantes soient triées automatiquement.
        self.__table_options__.setdefault('__provider_type_selector_type__', ProviderSelector)
        self.__table_options__.setdefault('__provider_type_selector__', ProviderSelector())
        self.__form_options__.setdefault('__provider_type_selector_type__', ProviderSelector)
        self.__form_options__.setdefault('__provider_type_selector__', ProviderSelector())

        # Personnalise le remplisseur de tableau afin que les "noms possibles"
        # (intitulés pouvant faire partie d'un nom d'attribut correspondant
        # au nom à afficher pour représenter l'objet) soient aussi utilisés
        # pour les attributs provenant de relations.
        self.table_filler = TableFiller(session)
        self.table_filler.__entity__ = self.model

        super(BaseSproxController, self).__init__(session, menu_items)

