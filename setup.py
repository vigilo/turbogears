# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
# Copyright (C) 2006-2012 CS-SI
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

tests_require = []

setup(
    name='vigilo-turbogears',
    version='2.1.2',
    author='Vigilo Team',
    author_email='contact@projet-vigilo.org',
    url='http://www.projet-vigilo.org/',
    license='http://www.gnu.org/licenses/gpl-2.0.html',
    description="Vigilo TurboGears extension library",
    long_description="This library provides the Vigilo extensions "
                     "to TurboGears 2",
    install_requires=[
        "setuptools",
        "repoze.tm2 >= 1.0a4",
        "repoze.what-quickstart >= 1.0",
        "repoze.what.plugins.sql",
        "repoze.what_pylons",
        "repoze.who_testutil",
        "repoze.who.plugins.sa",
        "repoze.who < 2.0dev",
        "tg.devtools < 2.1dev",
        "TurboGears2 >= 2.0b7",
        "TurboGears2 < 2.1dev",
        "sqlalchemy-migrate",
        "Pylons < 0.10dev",
        "ToscaWidgets >= 0.9.7.1",
        "Routes < 1.12",
        "tw.forms",
        "tw.rum < 0.3dev-20101203",
        "PasteDeploy",
        "Paste",
        "decorator != 3.1.0", # Blacklist bad version
        "vigilo-models",
        "vigilo-themes-default",
        "RumAlchemy < 0.4dev",
        "rum < 0.4dev",
        "TgRum",
        "python-ldap",
    ],
    paster_plugins=[
        'PasteScript',
        'Pylons',
        'TurboGears2',
#        'tg.devtools', # Provides migrate & quickstart commands.
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
        'rum.renderers': [
            'vigilo = vigilo.turbogears.rum.configuration:RumGenshiRenderer',
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
