# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2009, Gustavo Narea <me@gustavonarea.net>.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""Test utilities for repoze.who-powered applications."""

import sys
from logging import INFO
from re import compile as compile_regex

from zope.interface import implements
from paste.httpexceptions import HTTPUnauthorized
from paste.deploy.converters import asbool
from paste.response import remove_header

from repoze.who.middleware import PluggableAuthenticationMiddleware
from repoze.who.config import WhoConfig, \
                              make_middleware_with_config as mk_mw_cfg
from repoze.who.interfaces import IIdentifier, IAuthenticator, IChallenger

__all__ = ['AuthenticationForgerPlugin', 'AuthenticationForgerMiddleware',
           'make_middleware', 'make_middleware_with_config']


_HTTP_STATUS_PATTERN = compile_regex(r'^(?P<code>[0-9]{3}) (?P<reason>.*)$')


class AuthenticationForgerPlugin(object):
    """
    :mod:`repoze.who` plugin to forge authentication easily and bypass
    :mod:`repoze.who` challenges.

    This plugin enables you to write identifier and challenger-independent
    tests. As a result, your protected areas will be easier to test:

    #. To forge authentication, without bypassing identification (i.e., running
       MD providers), you can use the following WebTest-powered test::

           def test_authorization_granted(self):
               '''The right subject must get what she requested'''
               environ = {'REMOTE_USER': 'manager'}
               resp = self.app.get('/admin/', extra_environ=environ, status=200)
               assert 'some text' in resp.body

       As you can see, this is an identifier-independent way to forge
       authentication.

    #. To check that authorization was denied, in a challenger-independent way,
       you can use::

           def test_authorization_denied_anonymous(self):
               '''Anonymous users must get a 401 page'''
               self.app.get('/admin/', status=401)

           def test_authorization_denied_authenticated(self):
               '''Authenticated users must get a 403 page'''
               environ = {'REMOTE_USER': 'editor'}
               self.app.get('/admin/', extra_environ=environ, status=403)

    """

    implements(IIdentifier, IAuthenticator, IChallenger)

    def __init__(self, fake_user_key='REMOTE_USER',
                 remote_user_key='repoze.who.testutil.userid'):
        """

        :param fake_user_key: The key for the item in the ``environ`` which
            will contain the forged user Id.
        :type fake_user_key: str
        :param remote_user_key: The actual "external" ``remote_user_key``
            used by :mod:`repoze.who`.
        :type remote_user_key: str

        """
        self.fake_user_key = fake_user_key
        self.remote_user_key = remote_user_key

    # IIdentifier
    def identify(self, environ):
        """
        Pre-authenticate using the user Id found in the relevant ``environ``
        item, if any.

        The user Id. found will be put into ``identity['fake-userid']``, for
        :meth:`authenticate`.

        """
        if self.fake_user_key in environ:
            identity = {'fake-userid': environ[self.fake_user_key]}
            return identity

    # IIdentifier
    def remember(self, environ, identity):
        """Do nothing"""
        pass

    # IIdentifier
    def forget(self, environ, identity):
        """Do nothing"""
        pass

    # IAuthenticator
    def authenticate(self, environ, identity):
        """
        Turn the value in ``identity['fake-userid']`` into the remote user's
        name.

        Finally, it removes ``identity['fake-userid']`` so that it won't reach
        the WSGI application.

        """
        if 'fake-userid' in identity:
            environ[self.remote_user_key] = identity.pop('fake-userid')
            return environ[self.remote_user_key]

    # IChallenger
    def challenge(self, environ, status, app_headers, forget_headers):
        """Return a 401 page unconditionally."""
        headers = app_headers + forget_headers
        remove_header(headers, 'content-length')
        # The HTTP status code and reason may not be the default ones:
        status_parts = _HTTP_STATUS_PATTERN.search(status)
        if status_parts:
            reason = status_parts.group('reason')
            code = int(status_parts.group('code'))
        else:
            reason = 'HTTP Unauthorized'
            code = 401
        # Building the response:
        response = HTTPUnauthorized(headers=headers)
        response.title = reason
        response.code = code
        return response


class AuthenticationForgerMiddleware(PluggableAuthenticationMiddleware):
    """
    :class:`PluggableAuthenticationMiddleware
    <repoze.who.middleware.PluggableAuthenticationMiddleware>` proxy
    to forge authentication, without bypassing identification.

    """

    def __init__(self, app, identifiers, authenticators, challengers,
                 mdproviders, classifier, challenge_decider, log_stream=None,
                 log_level=INFO, remote_user_key='REMOTE_USER'):
        """
        Setup authentication in an easy to forge way.

        All the arguments received will be passed as is to
        :class:`repoze.who.middleware.PluggableAuthenticationMiddleware`,
        with one instance of :class:`AuthenticationForgerPlugin` in:

        * ``identifiers``. This instance will be inserted in the first position
          of the list.
        * ``authenticators``. Any authenticator passed will be ignored; such
          an instance will be the only authenticator defined.
        * ``challengers``. Any challenger passed will be ignored; such
          an instance will be the only challenger defined.

        Internally, it will also set ``remote_user_key`` to
        ``'repoze.who.testutil.userid'``, so that you can use the standard
        ``'REMOTE_USER'`` in your tests.

        The metadata providers won't be modified.

        """

        self.actual_remote_user_key = remote_user_key
        forger = AuthenticationForgerPlugin(fake_user_key=remote_user_key)
        forger = ('auth_forger', forger)
        identifiers.insert(0, forger)
        authenticators = [forger]
        challengers = [forger]
        # Calling the parent's constructor:
        init = super(AuthenticationForgerMiddleware, self).__init__
        init(app, identifiers, authenticators, challengers, mdproviders,
             classifier, challenge_decider, log_stream, log_level,
             'repoze.who.testutil.userid')


#{ Middleware makers:


def make_middleware(skip_authentication=False, *args, **kwargs):
    """
    Return the requested authentication middleware.

    :param skip_authentication: If ``True``, an instance of
        :class:`AuthenticationForgerMiddleware` will be returned instead of
        :class:`repoze.who.middleware.PluggableAuthenticationMiddleware`
    :type skip_authentication: bool

    ``args`` and ``kwargs`` are the positional and named arguments,
    respectively, to be passed to the relevant authentication middleware.

    """

    if asbool(skip_authentication):
        # We must replace the middleware:
        return AuthenticationForgerMiddleware(*args, **kwargs)
    else:
        return PluggableAuthenticationMiddleware(*args, **kwargs)


def make_middleware_with_config(app, global_conf, config_file, log_file=None,
                                log_level=None, skip_authentication=False):
    """
    Proxy :func:`repoze.who.config.make_middleware_with_config` to skip
    authentication when required.

    If  ``skip_authentication`` evaluates to ``True``, then the returned
    middleware will be an instance of :class:`AuthenticationForgerMiddleware`.

    """
    if not asbool(skip_authentication):
        # We must not replace the middleware
        return mk_mw_cfg(app, global_conf, config_file, log_file, log_level)

    # We must replace the middleware:
    parser = WhoConfig(global_conf['here'])
    parser.parse(open(config_file))
    return AuthenticationForgerMiddleware(
        app,
        parser.identifiers,
        parser.authenticators,
        parser.challengers,
        parser.mdproviders,
        parser.request_classifier,
        parser.challenge_decider,
        remote_user_key=parser.remote_user_key,
        )

#}
