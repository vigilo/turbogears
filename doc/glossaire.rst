Glossaire - Terminologie
------------------------

Ce chapitre recense les différents termes techniques employés dans ce document
et donne une brève définition de chacun de ces termes.

.. glossary::

    API (Application Programming Interface)
        Interface logicielle de programmation, permettant à un développeur
        d'enrichir la liste des fonctionnalités proposées par un logiciel.

    CGI (Common Gateway Interface)
        Interface standard de communication entre un serveur web et un
        programme capable de générer une réponse HTTP valide.
        Il s'agit par exemple de l'interface retenue par Nagios (< 3.3) pour
        la génération de ses pages web.

    CSS (Cascading Style Sheets)
        Feuilles de styles permettent de modifier la représentation graphique
        des éléments d'une page web. La version généralement supportée par les
        navigateurs est la version 2, définie par le document disponible sur
        http://www.w3.org/TR/CSS2/.

    CSV  (Comma-Separated Values)
        À l'origine, désigne un format textuel de transfert de données
        dans lequel les entrées sont séparées par des retours chariot
        et les champs par des virgules (comma). De nos jours, désigne
        plus généralement un format tabulé pour l'échange de données
        en vue de leur traitement dans un logiciel de type tableur
        ou par un traitement automatisé (scripts).

    DN (Distinguished Name)
        Identifiant unique dans le cadre d'un annuaire LDAP.

    Événement brut
        Alerte envoyée par Nagios au corrélateur de Vigilo pour analyse.

    Événement corrélé
        Incident détecté par Vigilo suite à la corrélation des alertes Nagios
        (évènements bruts).
        Un événement corrélé est causé par un unique événement brut
        (exemple : la panne d'un routeur), mais de nombreux autres évènements
        bruts peuvent lui être rattachés (exemple : les alertes indiquant que
        les serveurs situés derrière le routeur en panne sont indisponibles).
        Ces événements secondaires rattachés à l'événement corrélé sont alors
        appelés « événements bruts masqués ».

    KDC (Key Distribution Center)
        Serveur permettant un transfert sécurisé des clés de chiffrement
        utilisées pour les communications entre divers services. Ce serveur
        est notamment utilisé lors des échanges initiaux du protocole Kerberos.

    LDAP (Lightweight Directory Access Protocol)
        Protocole pour l'interrogation d'un annuaire, servant généralement à
        recenser les utilisateurs autorisés d'un système et les différentes
        propriétés associées à ces utilisateurs.

    OS (Operating System)
            Système d'exploitation.

    Nagios
        Composant libre de supervision système et réseau.

    RRD (Round Robin Database)
            Base de données de taille fixe utilisant des fichiers circulaires,
            dont les données sont progressivement compressées (avec perte) au
            fur et à mesure de leur vieillissement.

    RRDtool
        Composant libre de gestion de bases RRD (stockage, restitution,
        génération de graphiques).

    SGBD(R)
        Serveur de Gestion de Bases de Données (Relationnelles). Logiciel
        permettant d'héberger une base de données sur la machine.

    SQL (Structured Query Language)
        Langage de requêtes structuré pour l'interrogation d'une base de données
        relationnelle.

    URL (Uniform Resource Locator)
        Chaîne de caractères permettant d'identifier une ressource sur Internet.
        Exemple : http://www.projet-vigilo.org/

    WSGI (Web Server Gateway Interface)
        Une interface pour la communication entre une application et un serveur
        web, similaire à CGI. Il s'agit de l'interface utilisée par Vigilo.


.. vim: set tw=79 :
