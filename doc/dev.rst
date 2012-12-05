**********************
Guide de développement
**********************


Ajout de sous-contrôleurs personnalisés
=======================================

Les différentes interfaces web de Vigilo intègrent un contrôleur spécial
appelé ``custom`` et qui permet quant à lui d'intégrer des sous-contrôleurs
personnalisés.

Ces sous-contrôleurs doivent être déclarés en tant que points d'entrée
Python, au sein du groupe :samp:`{application}.controllers`, où *application*
correspond au nom en minuscules de l'application (par exemple, "vigiboard").
De plus, le nom du point d'entrée doit respecter les règles de nommage
suivantes :

-   Il doit être unique.
-   Il doit commencer par un caractère alphabétique (a-zA-Z).
-   Il ne doit être constitué que de caractères alphanumériques
    ou du symbole underscore (a-zA-Z0-9\_).

Le nom du point d'entrée deviendra le nom permettant d'accéder au
sous-contrôleur une fois celui-ci chargé. La valeur associée au point d'entrée
doit être le nom de la classe définissant le contrôleur à charger.
Celle-ci doit obligatoirement hériter de la classe
:py:class:`vigilo.turbogears.controllers.BaseController` pour être reconnue
comme étant un contrôleur valide.

Dans cet exemple, on supposera que la classe :py:class:`ExampleController`
contenue dans le module Python :py:mod:`my_ext.foo` est un contrôleur
qui étend l'application VigiBoard en fournissant une méthode ``test`` qui
affiche une page web d'exemple.
Pour ajouter ce contrôleur en tant que sous-contrôleur de ``custom`` avec
le nom ``example``, on utilisera la section ``entry_points`` suivante
dans le fichier :file:`setup.py` de définition du projet :

..  sourcecode:: python

    entry_points={
        'vigiboard.controllers': [
            'example = my_ext.foo:ExampleController',
            # Autres contrôleurs personnalisés à charger.
        ],
        # Autres groupes de points d'entrée.
    },

Une fois l'extension installée, il est nécessaire de recharger le processus
Apache à l'aide de la commande suivante :

..  sourcecode:: bash

    # Sous RedHat Enterprise Linux ou équivalent
    service httpd reload
    # Sous Debian ou équivalent
    service apache2 reload

La méthode ``test`` du nouveau sous-contrôleur est alors accessible à partir
de l'adresse http://example.com/vigilo/vigiboard/custom/example/test
(en supposant que VigiBoard a été installé à l'adresse
http://example.com/vigilo/vigiboard/)


Annexes
=======

..  include:: glossaire.rst


.. vim: set tw=79 :
