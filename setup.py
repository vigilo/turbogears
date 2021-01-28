# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
# Copyright (C) 2006-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import os, sys
from setuptools import setup, find_packages

cmdclass = {}
try:
    from babel.messages.frontend import compile_catalog as orig_compile_catalog
except ImportError:
    orig_compile_catalog = None

setup_requires = ['vigilo-common'] if not os.environ.get('CI') else []

def install_i18n(i18ndir, destdir):
    data_files = []
    langs = []
    for f in os.listdir(i18ndir):
        if os.path.isdir(os.path.join(i18ndir, f)) and not f.startswith("."):
            langs.append(f)
    for lang in langs:
        for f in os.listdir(os.path.join(i18ndir, lang, "LC_MESSAGES")):
            if f.endswith(".mo"):
                data_files.append(
                        (os.path.join(destdir, lang, "LC_MESSAGES"),
                         [os.path.join(i18ndir, lang, "LC_MESSAGES", f)])
                )
    return data_files

if orig_compile_catalog:
    class compile_catalog(orig_compile_catalog):
        def run(self):
            orig_compile_catalog.run(self)
            target_dir = os.path.join('src', 'vigilo', 'turbogears',
                                      'test_stack', 'i18n', 'fr', 'LC_MESSAGES')
            self.mkpath(target_dir)
            self.copy_file(
                os.path.join(self.directory, 'fr', 'LC_MESSAGES', self.domain + '.mo'),
                os.path.join(target_dir, 'vigilo.turbogears.test_stack.mo'),
                preserve_mode=False)
    cmdclass['compile_catalog'] = compile_catalog


tests_require = [
    'vigilo-models',    # Force le respect des contraintes de versions
                        # définies par vigilo-models sur SQLAlchemy.
    'WebTest',
    'lxml',
    'coverage',
    'gearbox',
]

setup(
    name='vigilo-turbogears',
    version='5.2.0',
    author='Vigilo Team',
    author_email='contact.vigilo@csgroup.eu',
    url='https://www.vigilo-nms.com/',
    license='http://www.gnu.org/licenses/gpl-2.0.html',
    description="Vigilo TurboGears extension library",
    long_description="This library provides the Vigilo extensions "
                     "to TurboGears 2",
    setup_requires=setup_requires,
    install_requires=[
        "setuptools",
        "repoze.tm2 >= 1.0a4",
        "repoze.who.plugins.sa",
        "repoze.who >= 2.0",
        "TurboGears2 >= 2.3.1",
        "TurboGears2 < 2.4dev",
        "ToscaWidgets >= 0.9.7.1",
        "tw.forms",
        "PasteDeploy",
        "Paste",
        "decorator != 3.1.0", # Blacklist bad version
        "vigilo-models",
        "vigilo-themes-default",
        "python-ldap",
        "WebOb >= 1.0",
        "tgext.crud >= 0.8.2",
        "zope.interface >= 4.0.0",
        "FormEncode >= 1.3.1",
        "backlash",
    ],
    namespace_packages = [
        'vigilo',
        ],
    packages=find_packages("src"),
    test_suite='nose.collector',
    tests_require=tests_require,
    extras_require={
        'tests': tests_require,
    },
    message_extractors={
        'src': [
            ('**.py', 'python', None),
        ],
    },
    entry_points={
        'paste.app_factory': [
            'main = vigilo.turbogears.test_stack.config:make_app',
        ],
    },
    cmdclass=cmdclass,
    package_dir={'': 'src'},
    vigilo_build_vars={
        'localstatedir': {
            'default': '/var',
            'description': "local state directory",
        },
    },
    data_files=
        install_i18n("i18n", os.path.join(sys.prefix, 'share', 'locale')) + [
        (os.path.join('@localstatedir@', 'cache', 'vigilo', 'sessions'), []),
    ],
)
