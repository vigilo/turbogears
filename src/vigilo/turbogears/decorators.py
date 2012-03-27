# -*- coding: utf-8 -*-

from tg import tmpl_context
from tg.decorators import Decoration
from tg.configuration import Bunch
from tg.util import partial
from webhelpers.paginate import Page
from pylons import request

class paginate(object):
    """Paginate a given collection.

    This decorator is mainly exposing the functionality
    of :func:`webhelpers.paginate`.

    X{Backport} de la version 2.1 (U{http://trac.turbogears.org/ticket/2302})
    """

    def __init__(self, name, use_prefix=False,
            items_per_page=10, max_items_per_page=0):
        self.name = name
        prefix = use_prefix and name + '_' or ''
        self.page_param = prefix + 'page'
        self.items_per_page_param = prefix + 'items_per_page'
        self.items_per_page = items_per_page
        self.max_items_per_page = max_items_per_page

    def __call__(self, func):
        decoration = Decoration.get_decoration(func)
        decoration.register_hook('before_validate', self.before_validate)
        decoration.register_hook('before_render', self.before_render)
        return func

    def before_validate(self, remainder, params):
        page = params.pop(self.page_param, None)
        if page:
            try:
                page = int(page)
                if page < 1:
                    raise ValueError
            except ValueError:
                page = 1
        else:
            page = 1
        request.paginate_page = page or 1
        items_per_page = params.pop(self.items_per_page_param, None)
        if items_per_page:
            try:
                items_per_page = min(
                    int(items_per_page), self.max_items_per_page)
                if items_per_page < 1:
                    raise ValueError
            except ValueError:
                items_per_page = self.items_per_page
        else:
            items_per_page = self.items_per_page
        request.paginate_items_per_page = items_per_page
        request.paginate_params = params.copy()
        if items_per_page != self.items_per_page:
            request.paginate_params[self.items_per_page_param] = items_per_page

    def before_render(self, remainder, params, output):
        if not isinstance(output, dict) or not self.name in output:
            return
        collection = output[self.name]
        page = Page(collection, request.paginate_page,
            request.paginate_items_per_page)
        page.kwargs = request.paginate_params
        if self.page_param != 'name':
            page.pager = partial(page.pager, page_param=self.page_param)
        if not getattr(tmpl_context, 'paginators', None):
            tmpl_context.paginators = Bunch()
        tmpl_context.paginators[self.name] = output[self.name] = page
