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

   DN (Distinguished Name)
        Identifiant unique dans le cadre d'un annuaire LDAP.

   KDC (Key Distribution Center)
        Serveur permettant un transfert sécurisé des clés de chiffrement
        utilisées pour les communications entre divers services. Ce serveur
        est notamment utilisé lors des échanges initiaux du protocole Kerberos.

   LDAP (Lightweight Directory Access Protocol)
        Protocole pour l'interrogation d'un annuaire, servant généralement à
        recenser les utilisateurs autorisés d'un système et les différentes
        propriétés associées à ces utilisateurs.

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
