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
    version='2.0.0',
    description='A package containing TurboGears modifications for Vigilo',
    author='Vigilo Team',
    author_email='contact@projet-vigilo.org',
    url='http://www.projet-vigilo.org/',
    license='http://www.gnu.org/licenses/gpl-2.0.html',
    install_requires=[
        "setuptools",
        "repoze.tm2 >= 1.0a4",
        "repoze.what-quickstart >= 1.0",
        "tg.devtools",
        "TurboGears2 >= 2.0b7",
        "ToscaWidgets >= 0.9.7.1",
        "tw.forms",
        "PasteDeploy",
        "Paste",
        "decorator != 3.1.0", # Blacklist bad version
        "vigilo-models",
        "vigilo-themes-default",
        "rum",
        "TgRum",
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
#    message_extractors={'vigilo.turbogears': [
#        ('**.py', 'python', None),
#    ]},
    entry_points={
        'rum.renderers': [
            'vigilo = vigilo.turbogears.rum.configuration:RumGenshiRenderer',
        ],
    },
    package_dir={'': 'src'},
)
