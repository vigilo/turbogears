# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

tests_require = ['WebTest', 'BeautifulSoup']

setup(
    name='vigilo-turbogears',
    version='0.1',
    description='A package containing TurboGears modifications for Vigilo',
    author='Francois POIROTTE',
    author_email='francois.poirotte@c-s.fr',
    #url='',
    install_requires=[
        "tg.devtools",
        "TurboGears2 >= 2.0b7",
        #can be removed iif use_toscawidgets = False
        "ToscaWidgets >= 0.9.7.1",
        "zope.sqlalchemy >= 0.4 ",
        #"repoze.tm2 >= 1.0a4",
        #"repoze.what-quickstart >= 1.0",
        "psycopg2",
        "vigilo-models",
        #"vigilo-themes-default",
        "PasteScript >= 1.7", # setup_requires has issues
        "PasteDeploy",
        "Paste",
        "decorator != 3.1.0", # Blacklist bad version
#        "modwsgideploy", # A des fins de tests
#        "repoze.who.plugins.vigilo.ldap", # A des fins de tests
        ],
    paster_plugins=['PasteScript', 'Pylons', 'TurboGears2', 'tg.devtools'],
    packages=find_packages(exclude=['ez_setup']),
    test_suite='nose.collector',
    tests_require=tests_require,
    extras_require={
        'tests': tests_require,
        },
#    message_extractors={'vigicore': [
#            ('**.py', 'python', None),
#        ]},
    entry_points={
#        'paste.app_factory': [
#            'main = vigicore.config.middleware:make_app',
#            ],
#        'paste.app_install': [
#            'main = pylons.util:PylonsInstaller',
#            ],
#        'console_scripts': [
#            'runtests-vigicore = vigicore.tests:runtests',
#            ],
        },
    package_dir={'': 'src'},
)