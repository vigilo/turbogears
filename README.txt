TurboGears
==========

Ce module contient les composants de Vigilo_ partagés entre les interfaces
web, qui sont basées sur TurboGears_. Il ne s'agit pas du framework TurboGears
lui-même, mais d'un jeu d'extensions et de composants communs aux interfaces
web Vigilo.

Pour les détails du fonctionnement de la bibliothèque TurboGears, se reporter
à la `documentation officielle`_.


Dépendances
-----------
Vigilo nécessite une version de Python supérieure ou égale à 2.5. Le chemin de
l'exécutable python peut être passé en paramètre du ``make install`` de la
façon suivante::

    make install PYTHON=/usr/bin/python2.6

La bibliothèque Vigilo-TurboGears a besoin des modules Python suivants :

- setuptools (ou distribute)
- vigilo-models
- vigilo-themes-default
- TurboGears >= 2.0b7 et < 2.1 (à patcher)
- repoze.tm2
- repoze.what-quickstart
- repoze.what.plugins.sql
- repoze.who_testutil
- repoze.who.plugins.sa
- tg.devtools
- ToscaWidgets >= 0.9.7.1
- tw.forms
- PasteDeploy
- Paste
- decorator (pas la version 3.1.0)
- rum < 0.4
- TgRum
- ToscaWidgets.rum

Des patches sont nécessaires pour les modules TurboGears et Pylons , ils se
trouvent dans le dossier "patches".


Installation
------------
L'installation se fait par la commande ``make install`` (à exécuter en
``root``).


License
-------
Vigilo-TurboGears est sous licence `GPL v2`_.


.. _documentation officielle: Vigilo_
.. _Vigilo: http://www.projet-vigilo.org
.. _TurboGears: http://turbogears.org
.. _GPL v2: http://www.gnu.org/licenses/gpl-2.0.html

.. vim: set syntax=rst fileencoding=utf-8 tw=78 :
