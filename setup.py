# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

tests_require = []

setup(
    name='vigilo-turbogears',
    version='0.1',
    description='A package containing TurboGears modifications for Vigilo',
    author='Vigilo Team',
    author_email='contact@projet-vigilo.org',
    url='http://www.projet-vigilo.org/',
    license='http://www.gnu.org/licenses/gpl-2.0.html',
    install_requires=[
        "repoze.tm2 >= 1.0a4",
        "repoze.what-quickstart >= 1.0",
#        "tg.devtools",
        "TurboGears2 >= 2.0b7",
        "ToscaWidgets >= 0.9.7.1",
        "PasteDeploy",
        "Paste",
        "decorator != 3.1.0", # Blacklist bad version
        "vigilo-models",
        "vigilo-themes-default",
    ],
    paster_plugins=[
        'PasteScript',
        'Pylons',
        'TurboGears2',
#        'tg.devtools', # Provides migrate & quickstart commands.
    ],
    packages=[
        'vigilo',
        'vigilo.turbogears',
        'vigilo.turbogears.controllers',
    ],
    test_suite='nose.collector',
    tests_require=tests_require,
    extras_require={
        'tests': tests_require,
    },
#    message_extractors={'vigilo.turbogears': [
#        ('**.py', 'python', None),
#    ]},
    entry_points={
    },
    package_dir={'': 'src'},
)
