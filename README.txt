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
Vigilo nécessite une version de Python supérieure ou égale à 2.7.

La bibliothèque Vigilo-TurboGears a besoin des modules Python suivants :

- setuptools
- vigilo-models
- vigilo-themes-default
- TurboGears >= 2.3.1
- repoze.tm2
- repoze.who_testutil
- repoze.who.plugins.sa
- ToscaWidgets >= 0.9.7.1
- tw.forms
- PasteDeploy
- Paste
- decorator (pas la version 3.1.0)
- FormEncode >= 1.3.0


Installation
------------
L'installation se fait par la commande ``python setup.py install``
(depuis le compte ``root``).


License
-------
Vigilo-TurboGears est sous licence `GPL v2`_.


.. _documentation officielle: Vigilo_
.. _Vigilo: https://www.vigilo-nms.com
.. _TurboGears: http://turbogears.org
.. _GPL v2: http://www.gnu.org/licenses/gpl-2.0.html

.. vim: set syntax=rst fileencoding=utf-8 tw=78 :


