# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
# Copyright (C) 2006-2019 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import os, sys

sysconfdir = os.getenv("SYSCONFDIR", "/etc")

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

tests_require = [
    'WebTest',
    'BeautifulSoup',
    'lxml',
    'coverage',
    'gearbox',
]

setup(
    name='vigilo-turbogears',
    version='5.1.0a1',
    author='Vigilo Team',
    author_email='contact.vigilo@c-s.fr',
    url='https://www.vigilo-nms.com/',
    license='http://www.gnu.org/licenses/gpl-2.0.html',
    description="Vigilo TurboGears extension library",
    long_description="This library provides the Vigilo extensions "
                     "to TurboGears 2",
    install_requires=[
        "setuptools",
        "repoze.tm2 >= 1.0a4",
        "repoze.who.plugins.sa",
        "repoze.who_friendlyform",
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
        "WebHelpers >= 1.0b4",
        "WebOb >= 1.0",
        "WebError >= 0.10.3",
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
    package_dir={'': 'src'},
    data_files= \
        install_i18n("i18n", os.path.join(sys.prefix, 'share', 'locale')) + [
        (
            os.path.join(sysconfdir, 'cron.daily'),
            [os.path.join('pkg', 'vigilo-clean-turbogears-sessions.sh')]
        ),
    ],
)
