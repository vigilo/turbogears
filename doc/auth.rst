*********************************
Authentification et autorisations
*********************************


Installation
============

Pré-requis logiciels
--------------------
La configuration de l'authentification dans Vigilo nécessite l'installation des
logiciels suivants :

* python (>= 2.5), sur la machine à configurer
* ``vigilo-turbogears``, installé automatiquement par les interfaces web de
  Vigilo

Reportez-vous aux manuels de ces différents logiciels pour savoir comment
procéder à leur installation sur votre machine.

Le paquet ``vigilo-turbogears`` requiert également la présence de plusieurs
dépendances Python. Ces dépendances seront automatiquement installées en même
temps que le paquet ``vigilo-turbogears``.


Comptes par défaut
==================

Un compte par défaut est créé lors de l'installation de Vigilo, appelé
« manager ». Ce compte correspond à un utilisateur disposant de tous les droits
(super-utilisateur). Il n'a pas vocation à être utilisé en cours
d'exploitation, mais plutôt à permettre des interventions ponctuelles liées à
des tâches d'administration.

Le mot de passe par défaut de ce compte est ``iddad``. Ce mot de passe peut
être modifié depuis une machine sur laquelle Vigilo est installé, via la ligne
de commandes en exécutant la commande vigilo-passwd, à partir du compte de
l'utilisateur ``root``.


Phases de l'authentification
============================

Le mécanisme d'authentification de Vigilo repose sur le framework
``repoze.who``. La gestion des autorisations repose sur le framework
``repoze.what``.

Les interfaces graphiques de Vigilo utilisent les prédicats définies dans
``repoze.what`` afin de restreindre l'accès à certaines fonctionnalités. Ces
prédicats peuvent nécessiter que l'utilisateur soit authentifié, appartienne à
un groupe d'utilisateurs particulier ou dispose d'une permission spéciale. Ce
document ne revient pas sur ce mécanisme de gestion des autorisations mais
insiste plutôt sur l'authentification de l'utilisateur, qui permet d'établir
les groupes auxquels il appartient et les permissions dont il dispose. Le
lecteur pourra consulter la documentation du projet ``repoze.what`` pour plus
d'information sur les mécanismes d'autorisation consulter `la documentation de
Repoze <http://what.repoze.org/docs/1.0/>`_.  L'authentification se déroule en
plusieurs phases :

- phase de classification, qui permet de savoir d'où provient la requête en
  cours de traitement (par exemple, provient-elle d'un navigateur web ou
  s'agit-il d'une requête interne à Vigilo ?),
- phase d'identification, chargée de reconnaître l'utilisateur lorsqu'il se
  connecte,
- phase d'authentification, chargée de vérifier l'identité de l'utilisateur,
- phase de « challenge », permettant de demander des informations à
  l'utilisateur afin de l'authentifier,
- phase d'enrichissement à l'aide de fournisseurs de méta-données, permettant
  d'associer des méta-données à la session de l'utilisateur authentifié.


Fichier de configuration
========================

La configuration de l'authentification se fait en créant un fichier INI. Ce
fichier INI utilise le format suivant:

.. sourcecode:: ini
    :linenos:

    [plugin:foo]
    use = bar.baz.foo:FooPlugin
    param_foo_1 = valeur1
    param_foo_2 = valeur2

    [general]
    request_classifier = bar.baz:Classifier
    challenge_decider = bar.baz:Challenger

    [identifiers]
    plugins =
        foo

    [authenticators]
    plugins =
        foo

    [challengers]
    plugins =
        foo

    [mdproviders]
    plugins =
        foo

La documentation du framework ``repoze.who`` contient
`de plus amples informations <http://docs.repoze.org/who/1.0/narr.html#middleware-configuration-via-config-file>`_.

Lien avec les phases de l'authentification
------------------------------------------
Le contenu du fichier de configuration suit de près les différentes phases de
l'authentification. Tout d'abord, des modules sont configurés, à l'aide de
sections ``plugin:``, puis ceux-ci sont associés aux différentes étapes de
l'authentification à l'aide des sections ``identifiers`` (identification),
``authenticators`` (authentification), ``challengers`` (challenge) et
``mdproviders`` (fournisseurs de méta-données).

La section ``general`` contient la configuration pour l'étape de
classification, ainsi que des paramètres généraux, qui ne sont pas liés aux
différentes étapes.

La suite de ce document décrit plus en détail le contenu des différentes
sections du fichier de configuration.

Sections ``plugin:``
--------------------
Les sections dont le nom commence par ``plugin:`` correspondent à la
configuration d'un module qui pourra être utilisé dans le cadre de la
configuration de l'authentification. Le libellé après les deux points « : »
correspond à un alias qui sera affecté au plugin.

La clé ``use`` permet de spécifier l'emplacement de la fonction ou de la classe
Python implémentant le module. L'emplacement du module est donné en utilisant
la syntaxe : ``module.python:ClassOuFonction``. Les autres clés de la section
correspondent aux différents paramètres attendus par le module.

Tous les modules définis par défaut dans *repoze.who* sont utilisables ici
[#]_.

.. [#] La liste complète des modules est disponible à l'adresse :
   http://docs.repoze.org/who/1.0/narr.html#module-repoze.who.plugins.sql

Vigilo fournit également le module d'identification et d'authentification
``repoze.who.plugins.vigilo.kerberos:VigiloKerberosAuthenticator`` permettant
d'utiliser un annuaire LDAP et la méthode Kerberos pour l'authentification des
utilisateurs.

Sections ``identifiers``, ``authenticators``, ``challengers`` et ``mdproviders``
--------------------------------------------------------------------------------
Les sections ``identifiers``, ``authenticators``, ``challengers`` et
``mdproviders`` permettent de définir les modules à utiliser au cours des
phases décrites au chapitre `Phases de l'authentification`_.

Chacune de ces sections ne contient qu'une seule clé, appelée ``plugins``,
qui contient la liste des modules à appeler, à l'aide des alias définis pour
ces modules lors de leur configuration (voir le chapitre
`Fichier de configuration`_).

La liste des modules doit être écrites à la ligne, indentée, avec un module par
ligne. Il est possible de n'appliquer un module que pour une classification
particulière (voir la fonction ``request_classifier`` décrite dans la
`Section general`_ du chapitre `Fichier de configuration`_) en
suffixant le nom du module par « ; » suivi de la classification pour laquelle
il agit.

Exemple de configuration possible pour les ``challengers``:

.. sourcecode:: ini
    :linenos:

    [challengers]
    plugins =
        friendlyform;browser
        basicauth;vigilo-api

Ici, le module ``friendlyform`` est appelé lorsque la fonction de
classification attribue la classification ``browser`` à la requête, tandis
qu'elle appelle le module ``basicauth`` lorsque la classification renvoyée est
``vigilo-api``.

Section ``general``
-------------------
La section ``general`` contient deux options :

- ``request_classifier`` permet de classer les requêtes (par exemple, selon
  leur origine). Il s'agit d'une fonction qui sera appelée à chaque requête et
  renvoie une chaîne de caractères décrivant la classification de la requête.
  Cette fonction est indiquée en utilisant la même syntaxe que pour la
  définition des modules, à savoir : ``module.python:ClasseOuFonction``.

  Vigilo fournit la fonction
  ``vigilo.turbogears.repoze_plugins:vigilo_classifier`` qui permet de
  distinguer les requêtes en fonction de leur origine/destination
  (navigation web, requêtes internes, interrogation de l'API de Vigilo, etc.)

- ``challenge_decider`` permet de définir une fonction qui sera appelée pour
  décider si la requête actuelle nécessite d'obtenir de plus amples
  informations sur l'utilisateur afin de pouvoir l'authentifier. Si la réponse
  est positive, alors les plugins définis dans la section ``challengers`` sont
  utilisés.

  Vigilo utilise le module de challenge standard de ``repoze.who`` (implémenté
  par la fonction ``repoze.who.classifiers:default_challenge_decider``) pour
  décider si des informations supplémentaires sont nécessaires au traitement de
  la demande d'authentification.

- ``remote_user_key`` indique la variable d'environnement provenant du serveur
  web qui contient l'identité de l'utilisateur authentifié. Cette valeur n'est
  utilisé que lorsqu'un mécanisme d'authentification externe est utilisé.
  Voir le chapitre :ref:`external_auth` pour plus d'information.

..  _vigilo_ldap:

Authentification LDAP
=====================

Ce chapitre explique comment configurer Vigilo afin d'utiliser un annuaire LDAP
pour authentifier les utilisateurs.

La configuration décrite ici est différente de celle proposée au chapitre
:ref:`apache_ldap`, car ici c'est Vigilo qui interroge l'annuaire lorsque
cela est nécessaire afin d'authentifier les utilisateurs, et non pas le serveur
web. Lorsqu'un nouvel utilisateur se connecte, le formulaire d'authentification
de Vigilo apparaîtra donc.

Avant de procéder à la configuration, contactez l'administrateur de l'annuaire
afin d'obtenir toutes les informations nécessaires à la connexion. A minima :

*   Adresse ou nom d'hôte qualifié de l'annuaire,
*   Port / protocole (LDAP ou LDAPS)
*   Nom distingué des branches de l'annuaire contenant les utilisateurs
    et les groupes
*   Filtres à appliquer pour rechercher les utilisateurs et les groupes
*   Noms des attributs dans l'annuaire correspondant aux informations suivantes
    pour un utilisateur donné :

    *   Identifiant de l'utilisateur
    *   Adresse électronique de l'utilisateur
    *   Nom commun de l'utilisateur
    *   Liste des groupes dont l'utilisateur est membre (si l'annuaire utilise
        ce mécanisme)

*   Noms des attributs dans l'annuaire correspondant aux informations suivantes
    pour un groupe donné :

    *   Nom commun du groupe
    *   Liste des membres du groupe (si l'annuaire utilise ce mécanisme)

Pour utiliser l'authentification LDAP de Vigilo,
:ref:`configurer le greffon de synchronisation LDAP <ldap_sync>`.

Ajouter ensuite l'instance ainsi créée à la liste des greffons
d'authentification dans le fichier :file:`who.ini` :

..  sourcecode:: ini

    [authenticators]
    plugins =
        vigilo.turbogears.repoze.plugins.sqlauth:plugin
        auth_tkt
        ldapsync

Ici, ``ldapsync`` correspond au nom donné à l'instance du greffon
de synchronisation LDAP configuré en suivant les instructions du chapitre
:ref:`ldap_sync`.

Pour que l'utilisateur et ses groupes soient automatiquement importés
dans Vigilo, ajouter l'instance aux fournisseurs de méta-données :

..  sourcecode:: ini

    [mdproviders]
    plugins =
        ldapsync
        vigilo.turbogears.repoze.plugins.mduser:plugin

L'opération doit être répétée pour chacune des interfaces web.


Authentification externe
========================

Vigilo supporte l'authentification externe. Dans ce mode, l'authentification
est réalisée par le serveur web Apache, plutôt qu'en utilisant la base de
comptes interne de Vigilo. Le serveur web transmet ensuite l'identité de
l'utilisateur authentifié à Vigilo.

Ce mode d'authentification permet par exemple d'authentifier les utilisateurs
en utilisant les protocoles suivants :

*   LDAP
*   Kerberos

Lorsque l'authentification externe est configurée, il est ensuite possible
de récupérer les groupes auxquels appartient l'utilisateur authentifié depuis
un annuaire LDAP, et ce indépendamment du mode d'authentification configuré
au niveau du serveur web.

Dans ce chapitre, nous allons détailler différentes configurations s'appuyant
sur l'authentification externe.

Avant de pouvoir commencer, le support de l'authentification externe doit être
activé dans Vigilo en suivant la procédure du chapitre :ref:`external_auth`.

.. _external_auth:

Activation de l'authentification externe dans Vigilo
----------------------------------------------------

L'activation de l'authentification externe dans les interfaces web de Vigilo
se fait en éditant le fichier :file:`who.ini` de l'interface web visée.

Lorsque l'authentification externe est activée, Vigilo s'attend à ce que le
serveur web lui transmette l'identifiant de l'utilisateur identifié via
une variable d'environnement WSGI. Par défaut, la variable d'environnement
``REMOTE_USER`` est utilisée.

..  warning::

    L'authentification externe suppose que tous les accès aux interfaces de
    Vigilo se font après authentification par le serveur web.

    N'activez jamais l'authentification externe si les utilisateurs ont la
    possibilité d'accéder aux interfaces de Vigilo en contournant
    l'authentification configurée au niveau du serveur web (par exemple,
    au moyen d'une URL alternative). Cela ouvrirait une faille de sécurité.

Pour activer l'authentification externe :

* Instancier le greffon ``vigilo.turbogears.repoze.plugins.externalid:ExternalIdentification`` :

    ..  sourcecode:: ini

        [plugin:externalid]
        use = vigilo.turbogears.repoze.plugins.externalid:ExternalIdentification
        rememberer = auth_tkt

    ``plugin:externalid`` permet de créer une nouvelle instance d'un greffon.
    Le libellé se trouvant après « : » (ici, ``externalid``) affecte un nom
    à l'instance (pour pouvoir y faire référence par la suite).

    Les paramètres du greffon sont les suivants :

    ..  list-table:: Paramètres du greffon vigilo.turbogears.repoze.plugins.externalid:ExternalIdentification
        :widths: 15 15 10 60
        :header-rows: 1

        * - Paramètre
          - Type
          - Obligatoire ?
          - Description

        * - ``encoding``
          - Chaîne de caractères
          - non
          - Indique le nom de l'encodage de caractères utilisé par le serveur web
            pour représenter l'identifiant de l'utilisateur.

            La valeur par défaut est ``UTF-8``.

        * - ``rememberer``
          - Chaîne de caractères
          - oui
          - Indique le nom du greffon chargé de mémoriser l'identité de l'utilisateur
            après la première authentification (pour éviter de le réauthentifier
            à chaque chargement de page).

        * - ``strip_realm``
          - Booléen
          - non
          - Indique si le nom du royaume / domaine d'authentification doit être
            retiré ou non de l'identifiant avant d'être utilisé par Vigilo.
            Cette option est activée par défaut.

            Si ce paramètre est activé et que l'utilisateur ``foobar@EXAMPLE.COM``
            se connecte, alors seul ``foobar`` sera utilisé comme identifiant
            de l'utilisateur dans Vigilo.

        * - ``use``
          - Chaîne de caractères
          - oui
          - Définit le greffon à instancier.

            Utiliser ``vigilo.turbogears.repoze.plugins.externalid:ExternalIdentification``.

*   Ajouter l'instance à la liste des greffons utilisée pour identifier les
    utilisateurs, par exemple :

    ..  sourcecode:: ini

        [identifiers]
        plugins =
            friendlyform;browser,internal
            basicauth;vigilo-api
            auth_tkt
            externalid

    Ici, ``externalid`` correspond au nom de l'instance précédemment créée.

*   Ajouter l'instance à la liste des greffons utilisée pour authentifier les
    utilisateurs, par exemple :

    ..  sourcecode:: ini

        [authenticators]
        plugins =
            vigilo.turbogears.repoze.plugins.sqlauth:plugin
            auth_tkt
            externalid

    Là encore, ``externalid`` correspond au nom de l'instance précédemment créée.

*   Le cas échéant, modifier le nom de la variable d'environnement à utiliser
    pour obtenir l'identifiant de l'utilisateur en positionnant l'option
    ``remote_user_key`` de la section ``[general]``. Par exemple, pour utiliser
    la variable d'environnement ``HTTP_REMOTE_USER`` :

    ..  sourcecode:: ini

        [general]
        request_classifier = vigilo.turbogears.repoze.classifier:vigilo_classifier
        challenge_decider = repoze.who.classifiers:default_challenge_decider
        remote_user_key = HTTP_REMOTE_USER

..  _apache_ldap:

Exemple 1 : Authentification LDAP via Apache
--------------------------------------------

Dans ce chapitre, nous allons mettre en place une authentification basée
sur un annuaire LDAP, en utilisant le serveur web Apache pour réaliser
l'authentification.

Contrairement à la configuration du chapitre :ref:`vigilo_ldap`, l'authentification
est ici réalisée par le serveur web. Lorsqu'un nouvel utilisateur se connecte,
il sera invité à saisir son identifiant / mot de passe via une boîte de dialogue
présentée par le navigateur.

Avant de procéder à la configuration, contactez l'administrateur de l'annuaire
afin d'obtenir toutes les informations nécessaires à la connexion. A minima :

*   Adresse ou nom d'hôte qualifié de l'annuaire,
*   Port / protocole (LDAP ou LDAPS)
*   Nom distingué des branches de l'annuaire contenant les utilisateurs
    et les groupes
*   Filtres à appliquer pour rechercher les utilisateurs et les groupes
*   Noms des attributs dans l'annuaire correspondant aux informations suivantes
    pour un utilisateur donné :

    *   Identifiant de l'utilisateur
    *   Adresse électronique de l'utilisateur
    *   Nom commun de l'utilisateur
    *   Liste des groupes dont l'utilisateur est membre (si l'annuaire utilise
        ce mécanisme)

*   Noms des attributs dans l'annuaire correspondant aux informations suivantes
    pour un groupe donné :

    *   Nom commun du groupe
    *   Liste des membres du groupe (si l'annuaire utilise ce mécanisme)

Afin d'utiliser LDAP comme méthode d'authentification, le serveur web
Apache doit être reconfiguré. La configuration qui suit se base sur le module
``mod_authnz_ldap``.

Si le module ``mod_authnz_ldap`` n'est pas encore installé sur la machine
qui héberge le serveur web, l'installer en utilisant les outils prévus
par la distribution.

Le listing suivant montre la configuration à mettre en place dans le fichier
de configuration Apache de VigiBoard (:file:`/etc/httpd/conf.d/vigiboard.conf`)
pour authentifier les utilisateurs en utilisant le protocole LDAP :

.. sourcecode:: apache
    :linenos:

    <IfModule !mod_authnz_ldap.c>
        LoadModule authnz_ldap_module extramodules/mod_authnz_ldap.so
    </IfModule>

    <IfModule !mod_wsgi.c>
        LoadModule wsgi_module modules/mod_wsgi.so
    </IfModule>

    <IfModule mod_wsgi.c>
        WSGISocketPrefix        /var/run/wsgi
        WSGIRestrictStdout      off
        WSGIPassAuthorization   on
        WSGIDaemonProcess       vigiboard user=apache group=apache processes=4 threads=1 display-name=vigilo-vigiboard
        WSGIScriptAlias         /vigilo/vigiboard "/etc/vigilo/vigiboard/vigiboard.wsgi"

        KeepAlive Off

        <Directory "/etc/vigilo/vigiboard/">
            <IfModule mod_headers.c>
                Header set X-UA-Compatible "IE=edge"
            </IfModule>

            <Files "vigiboard.wsgi">
                WSGIProcessGroup vigiboard
                WSGIApplicationGroup %{GLOBAL}
                <IfModule mod_authz_core.c>
                    # Apache 2.4
                    Require all granted
                </IfModule>
                <IfModule !mod_authz_core.c>
                    # Apache 2.2
                    Order Deny,Allow
                    Allow from all
                </IfModule>
            </Files>
        </Directory>

        <Location "/vigilo/vigiboard/">
            AuthType                basic
            AuthBasicProvider       ldap
            AuthName                "LDAP"
            AuthLDAPURL             "ldap://ldap.example.com/cn=Users,dc=example,dc=com?samaccountname?sub?(objectClass=*)"
            AuthLDAPBindDN          "cn=Authentication,cn=Users,dc=example,dc=com"
            AuthLDAPBindPassword    "mypassword"
            Require                 valid-user
        </Location>
    </IfModule>

Avec cette configuration, seule l'URL
``http://vigilo.example.com/vigilo/vigiboard/login`` est protégée par une
authentification LDAP. Les autres pages redirigent vers celle-ci
lorsqu'un utilisateur authentifié est attendu et que l'utilisateur courant
ne l'est pas. Cette solution offre le meilleur compromis possible entre la
sécurité (il n'est pas possible d'accéder à une ressource protégée sans être
authentifié) et les performances (une seule authentification par session).

Voici les modifications apportées par rapport à la configuration par défaut :

*   Les lignes 1 à 3 permettent de charger le module ``mod_authnz_ldap``
    qui sera utilisé par l'authentification.

*   Les lignes 38 à 46 activent l'authentification LDAP pour toutes les pages
    de VigiBoard.

Le tableau suivant détaille les options de configuration utilisées :

..  list-table:: Options de configuration relatives à l'authentification LDAP
    :widths: 20 20 60
    :header-rows: 1

    * - Directive
      - Type
      - Description

    * - ``AuthType``
      - Chaîne de caractères
      - Indique le type d'authentification à utiliser.
        Utiliser ``basic`` dans le cas de l'authentification LDAP.

    * - ``AuthBasicProvider``
      - Chaîne de caractères
      - Indique le nom du module qui effectuera l'authentification.
        Utiliser ``ldap`` dans le cas de l'authentification LDAP.

    * - ``AuthName``
      - Chaîne de caractères
      - Permet d'associer un nom à cette méthode d'authentification.
        Ce nom apparaîtra dans les journaux d'événements du serveur web.

    * - ``AuthLDAPURL``
      - Chaîne de caractères
      - Spécifie l'URL de connexion à l'annuaire LDAP, au format
        ``ldap://host:port/basedn?attribute?scope?filter``.

    * - ``AuthLDAPBindDN``
      - Chaîne de caractères
      - Nom distingué du compte utilisé pour la connexion à l'annuaire LDAP.

    * - ``AuthLDAPBindPassword``
      - Chaîne de caractères
      - Mot de passe utilisé pour la connexion à l'annuaire LDAP.

    * - ``Require``
      - Chaîne de caractères
      - Indique les conditions pour que l'utilisateur ait accès à l'interface web.
        La valeur ``valid-user`` limite l'accès aux utilisateurs qui disposent
        d'un compte valide dans l'annuaire LDAP.

La documentation du module `mod_authnz_ldap <https://httpd.apache.org/docs/current/en/mod/mod_authnz_ldap.html>`_
contient de nombreuses directives supplémentaires qui peuvent être utilisées
pour configurer très finement le mécanisme d'authentification.
Il est recommandé de s'y référer pour plus d'information.

..  note::

    Par défaut, le module ``mod_authnz_ldap`` d'Apache transmet l'identité
    de l'utilisateur authentifié à Vigilo via une variable d'environnement
    nommée :envvar:`AUTHENTICATE_<attr>``, où ``<attr>`` correspond au nom
    de l'attribut dans l'annuaire contenant l'identifiant, en majuscules.

    Par conséquent, il est généralement nécessaire de modifier la valeur
    de l'option ``remote_user_key`` dans le fichier :file:`who.ini`.
    Se référer au chapitre :ref:`external_auth` pour plus d'information.

    Par exemple, si l'attribut ``sAMAccountName`` d'Active Directory est utilisé
    pour identifier les utilisateurs, on positionnera ``remote_user_key`` à la
    valeur ``AUTHENTICATE_SAMACCOUNTNAME``.

La même configuration doit être réalisée pour les différentes interfaces web
de Vigilo déployées sur la machine (VigiAdmin, VigiBoard, VigiMap, VigiGraph),
en adaptant l'URL de la ressource à protéger.

Une fois le serveur web configuré, il est nécessaire de le redémarrer pour que
la nouvelle configuration soit prise en compte.


Exemple 2 : Authentification Kerberos
-------------------------------------

Dans ce chapitre, nous allons mettre en place une authentification unique
(Single Sign-On) basée sur le protocole Kerberos.

On suppose que l'infrastructure Kerberos nécessaire (KDC) est déjà en place
et que les informations permettant au serveur web d'interagir avec l'infrastructure
Kerberos (nom du service, nom du royaume Kerberos et fichier keytab) sont connues.

.. _apache_kerberos:

Configuration d'Apache
~~~~~~~~~~~~~~~~~~~~~~

Afin d'utiliser Kerberos comme méthode d'authentification, le serveur web
Apache doit être reconfiguré. La configuration qui suit se base sur le module
``mod_auth_kerb``.

Si le moodule ``mod_auth_kerb`` n'est pas encore installé sur la machine
qui héberge le serveur web, l'installer en utilisant les outils prévus
par la distribution.

Le listing suivant montre la configuration à mettre en place dans le fichier
de configuration Apache de VigiBoard (:file:`/etc/httpd/conf.d/vigiboard.conf`)
pour authentifier les utilisateurs en utilisant le protocole Kerberos :

.. sourcecode:: apache
    :linenos:

    <IfModule !mod_auth_kerb.c>
        LoadModule auth_kerb_module extramodules/mod_auth_kerb.so
    </IfModule>

    <IfModule !mod_wsgi.c>
        LoadModule wsgi_module modules/mod_wsgi.so
    </IfModule>

    <IfModule mod_wsgi.c>
        WSGISocketPrefix        /var/run/wsgi
        WSGIRestrictStdout      off
        WSGIPassAuthorization   on
        WSGIDaemonProcess       vigiboard user=apache group=apache processes=4 threads=1 display-name=vigilo-vigiboard
        WSGIScriptAlias         /vigilo/vigiboard "/etc/vigilo/vigiboard/vigiboard.wsgi"

        KeepAlive Off

        <Directory "/etc/vigilo/vigiboard/">
            <IfModule mod_headers.c>
                Header set X-UA-Compatible "IE=edge"
            </IfModule>

            <Files "vigiboard.wsgi">
                WSGIProcessGroup vigiboard
                WSGIApplicationGroup %{GLOBAL}
                <IfModule mod_authz_core.c>
                    # Apache 2.4
                    Require all granted
                </IfModule>
                <IfModule !mod_authz_core.c>
                    # Apache 2.2
                    Order Deny,Allow
                    Allow from all
                </IfModule>
            </Files>
        </Directory>

        <Location "/vigilo/vigiboard/login">
            AuthType            kerberos
            AuthName            "Kerberos"
            KrbServiceName      HTTP
            KrbAuthRealms       EXAMPLE.COM
            Krb5Keytab          /etc/httpd/conf/HTTP.vigilo.example.com.keytab
            KrbMethodNegotiate  on
            KrbMethodK5Passwd   on
            KrbSaveCredentials  on
            KrbVerifyKDC        on
            Require             valid-user
        </Location>
    </IfModule>

Avec cette configuration, seule l'URL
``http://vigilo.example.com/vigilo/vigiboard/login`` est protégée par une
authentification Kerberos. Les autres pages redirigent vers celle-ci
lorsqu'un utilisateur authentifié est attendu et que l'utilisateur courant
ne l'est pas. Cette solution offre le meilleur compromis possible entre la
sécurité (il n'est pas possible d'accéder à une ressource protégée sans être
authentifié) et les performances (une seule authentification par session).

Voici les modifications apportées par rapport à la configuration par défaut :

*   Les lignes 1 à 3 permettent de charger le module ``mod_auth_kerb``
    qui sera utilisé par l'authentification.

*   Les lignes 38 à 49 activent l'authentification Kerberos pour la ressource
    ``/vigilo/vigiboard/login``.

Le tableau suivant détaille les options de configuration utilisées :

..  list-table:: Options de configuration relatives à l'authentification Kerberos
    :widths: 20 20 60
    :header-rows: 1

    * - Directive
      - Type
      - Description

    * - ``AuthType``
      - Chaîne de caractères
      - Indique le type d'authentification à utiliser.
        Utiliser ``kerberos`` dans le cas de l'authentification Kerberos.

    * - ``AuthName``
      - Chaîne de caractères
      - Permet d'associer un nom à cette méthode d'authentification.
        Ce nom apparaîtra dans les journaux d'événements du serveur web.

    * - ``KrbServiceName``
      - Chaîne de caractères
      - Correspond au nom du service défini dans Kerberos pour le
        serveur web. La valeur par défaut est « HTTP ».

        Il est recommandé de ne modifier cette valeur que si vous savez
        exactement ce que vous faites.

    * - ``KrbAuthRealms``
      - Chaîne de caractères
      - Indique le nom du royaume Kerberos dans lequel l'authentification
        a lieu. Ce nom s'écrit toujours **en majuscules**.

    * - ``Krb5Keytab``
      - Chaîne de caractères
      - Spécifie l'emplacement du fichier contenant la clé secrète
        d'authentification (keytab) du serveur web.
        Ce fichier doit être accessible uniquement par le serveur web.

    * - ``KrbMethodNegotiate``
      - Booléen
      - Autorise la négociation de la méthode d'authentification entre
        le navigateur et le serveur web.

        Pour des raisons de compatibilité avec les différents navigateurs
        web, il est recommandé d'autoriser la négociation.

    * - ``KrbMethodK5Password``
      - Booléen
      - Permet d'autoriser ou non l'utilisateur à s'authentifier
        en utilisant un identifiant et un mot de passe, dans le cas
        où il ne dispose pas déjà d'un jeton Kerberos valide.

        Il est recommandé d'autoriser ce mécanisme, sauf si Kerberos est
        également utilisé pour authentifier l'utilisateur au moment de
        l'ouverture de session sur son poste de travail. Dans ce cas,
        le fait de désactiver ce mécanisme améliore la sécurité en évitant
        les tentatives d'attaques par force brute sur le mot de passe
        de l'utilisateur.

        Si ce mécanisme est activé, il est recommandé d'activer TLS sur le
        serveur web pour sécuriser le transfert de l'identifiant et du mot
        de passe.

    * - ``KrbSaveCredentials``
      - Booléen
      - Permet de sauvegarder temporairement le ticket Kerberos de
        l'utilisateur sur le serveur web afin de permettre à l'application
        d'interroger d'autres services en utilisant Kerberos avec
        l'identité de l'utilisateur (délégation).

        Cette option est nécessaire dans les interfaces graphiques lorsque
        l'accès à Nagios se fait via une authentification Kerberos,
        afin de propager le ticket Kerberos reçu et maintenir la traçabilité
        des accès. Le fichier temporaire contenant le ticket Kerberos est
        supprimé automatiquement à la fin de la requête.

    * - ``KrbVerifyKdc``
      - Booléen
      - Désactive la vérification de l'identité du KDC.
        Pour plus de sécurité, il est recommandé de positionner cette
        directive à la valeur « on ». L'activation de cette option
        nécessite cependant une configuration plus avancée de l'infrastructure
        Kerberos, qui dépasse le cadre de ce document.

    * - ``Require``
      - Chaîne de caractères
      - Indique les conditions pour que l'utilisateur ait accès à l'interface web.
        La valeur ``valid-user`` limite l'accès aux utilisateurs qui disposent
        d'un compte valide dans la base Kerberos.

La documentation du module `mod_auth_kerb <http://modauthkerb.sourceforge.net/configure.html>`_
décrit les autres directives qui peuvent être utilisées pour configurer le processus
d'authentification de manière plus précise.
Il est recommandé de s'y référer pour plus d'information.

La même configuration doit être réalisée pour les différentes interfaces web
de Vigilo déployées sur la machine (VigiAdmin, VigiBoard, VigiMap, VigiGraph),
en adaptant l'URL de la ressource à protéger.

Une fois le serveur web configuré, il est nécessaire de le redémarrer pour que
la nouvelle configuration soit prise en compte.

Configuration du navigateur web des exploitants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Mozilla Firefox
^^^^^^^^^^^^^^^
L'activation de l'authentification par Kerberos dans Firefox se fait en
modifiant 2 options dans la configuration. La configuration actuelle de Firefox
peut être affichée en ouvrant un nouvel onglet, en tapant ``about:config``
dans la barre d'adresse et en validant.

Un message de mise en garde s'affiche, comme sur l'illustration intitulée
`Avertissement de Mozilla Firefox`_.

.. _`Avertissement de Mozilla Firefox`:
.. figure:: img/firefox-warn.png

   Avertissement de Mozilla Firefox

Après prise en compte de l'avertissement (« Je ferai attention, promis ! »), la
configuration actuelle de Firefox s'affiche, comme sur l'illustration intitulée
`Options de configuration de Firefox`_.

.. _`Options de configuration de Firefox`:
.. figure:: img/firefox-options.png

   Options de configuration de Firefox

Dans la barre de filtrage des options (encadrée en rouge sur l'illustration
intitulée `Options de configuration de Firefox`_), saisir « negotiate-auth ».
Les paramètres actuels relatifs à l'authentification Kerberos (via le protocole
GSSAPI) s'affichent dans la zone de résultats, comme sur l'illustration
intitulée `Options relatives à l'authentification Kerberos`_.

.. _`Options relatives à l'authentification Kerberos`:
.. figure:: img/firefox-kerberos.png

   Options relatives à l'authentification Kerberos

Les options à modifier, leur description et la valeur à utiliser sont
récapitulées ci-dessous :

network.negotiate-auth.delegation-uris
    Liste les adresses Internet pour lesquelles la délégation du ticket
    Kerberos est autorisée. La délégation du ticket doit être autorisée pour
    utiliser correctement les interfaces graphiques de Vigilo.

    Exemple : ``https://,vigilo.example.com``. Cette valeur autorise la
    délégation du ticket pour les sites utilisant une connexion chiffrée
    (HTTPS) *ou* à destination du serveur ``vigilo.example.com``.

network.negotiate-auth.trusted-uris
    Liste les adresses Internet pour lesquelles un ticket Kerberos doit être
    transmis.

    Exemple : ``https://,localhost,vigilo.example.com``. Cette valeur autorise
    la transmission du ticket aux sites utilisant une connexion chiffrée
    (HTTPS) *ou* à destination du serveur ``vigilo.example.com``.

L'illustration suivante montre un exemple de configuration autorisant
l'authentification Kerberos pour les sites hébergés par
``vigilo.example.com``.

.. _`Configuration autorisant l'authentification Kerberos vers Vigilo`:
.. figure:: img/firefox-kerberos-vigilo.png

   Configuration autorisant l'authentification Kerberos vers Vigilo

Microsoft Internet Explorer
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Depuis Windows XP, la prise en charge de Kerberos dans Internet Explorer
nécessite uniquement l'activation du mécanisme d'Authentification Intégrée de
Windows.

L'activation se fait en allant dans le menu « Outil » et en sélectionnant
« Options Internet ». La boîte de dialogue des options d'Internet Explorer
s'ouvre alors (voir illustration intitulée
`Options de Microsoft Internet Explorer`_).

.. _`Options de Microsoft Internet Explorer`:
.. figure:: img/ie-options.png

   Options de Microsoft Internet Explorer

Cliquer sur l'onglet « Avancées » (en rouge sur l'illustration intitulée
`Options de Microsoft Internet Explorer`_), puis faire défiler les options
jusqu'à trouver la ligne « Activer l'authentification Windows intégrée »
(encadrée en rouge sur l'illustration intitulée
`Activation de la prise en charge de Kerberos`_). L'option doit être
cochée pour que l'authentification par Kerberos soit supportée.

.. _`Activation de la prise en charge de Kerberos`:
.. figure:: img/ie-kerberos.png

   Activation de la prise en charge de Kerberos

Une fois la prise en charge de Kerberos activée, valider la modification en
cliquant sur le bouton « OK » et redémarrer Internet Explorer.

Vérification du bon fonctionnement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
La manière la plus simple de vérifier le bon fonctionnement de l'authentification
Kerberos consiste simplement à se connecter à l'une des interfaces web de Vigilo.

Si vous ne disposez pas encore d'un ticket Kerberos valide et que la directive
``KrbMethodK5Passwd`` a été positionnée à « on » sur le serveur (voir le
chapitre :ref:`apache_kerberos`), une boîte de dialogue vous invite à vous
authentifier à l'aide de votre identifiant et de votre mot de passe.

En revanche, si cette directive a été positionnée à « off », l'authentification
échoue et une page d'erreur apparaît dans le navigateur. Dans ce cas, vous
devez d'abord obtenir un ticket Kerberos pour accéder à l'application.

Sous Linux, vous pouvez obtenir un ticket Kerberos à l'aide de la commande
suivante::

    $ kinit -f <identifiant Kerberos>

L'option « -f » indique que le ticket peut être réutilisé par les services
auxquels vous vous connectez (délégation). Elle est nécessaire au bon
fonctionnement des interfaces de Vigilo.

..  _ldap_sync:

Synchronisation avec un annuaire LDAP
-------------------------------------

Une fois l'utilisateur authentifié depuis une source d'authentification externe,
il est possible de configurer Vigilo afin de récupérer automatiquement
certaines informations associées à l'utilisateur authentifié depuis un annuaire LDAP.

Les informations récupérées depuis l'annuaire LDAP sont :

*   Le nom usuel de l'utilisateur ;
*   L'adresse email de l'utilisateur ;
*   La liste des groupes auxquels l'utilisateur appartient.

La resynchronisation des informations n'est réalisée que lors de l'ouverture
d'une nouvelle session. Les changements opérés dans l'annuaire concernant
les groupes auxquels l'utilisateur appartient ne s'appliqueront donc qu'à
la connexion suivante de l'utilisateur sur Vigilo.

..  note::

    La récupération des informations depuis un annuaire LDAP n'est possible que
    lorsque l'authentification provient d'une source d'authentification externe.
    Il n'est pas possible de combiner l'authentification utilisant la base
    interne de Vigilo avec ce mécanisme de synchronisation LDAP.

La synchronisation des informations se fait en configurant le greffon
``vigilo.turbogears.repoze.plugins.mdldapsync:VigiloLdapSync``
dans le fichier :file:`who.ini` de l'interface web visée :

Exemple de configuration du greffon :

..  sourcecode:: ini

    [plugin:ldapsync]
    use = vigilo.turbogears.repoze.plugins.mdldapsync:VigiloLdapSync
    ldap_url = ldap://ldap.example.com
    users_base = ou=people,dc=example,dc.com
    groups_base = ou=people,dc=example,dc.com
    user_filter = (objectClass=person)
    group_filter = (objectClass=group)
    binddn = mybinduser
    bindpw = mybindpassword
    timeout = 3

``plugin:ldapsync`` permet de créer une nouvelle instance du greffon
et de la nommer (ici, l'instance s'appelle ``ldapsync``).

Les paramètres du greffon sont les suivants :

..  list-table:: Paramètres du greffon vigilo.turbogears.repoze.plugins.mdldapsync:VigiloLdapSync
    :widths: 15 15 10 60
    :header-rows: 1

    * - Paramètre
      - Type
      - Obligatoire ?
      - Description

    * - ``attr_cn``
      - Chaîne de caractères
      - non
      - Indique le nom de l'attribut dans la fiche de l'utilisateur qui contient
        son nom usuel. La valeur par défaut est ``cn``.

    * - ``attr_group_cn``
      - Chaîne de caractères
      - non
      - Indique le nom de l'attribut dans la fiche d'un groupe qui contient
        son nom usuel. La valeur par défaut est ``cn``.

    * - ``attr_group_member``
      - Chaîne de caractères
      - non
      - Indique le nom de l'attribut dans la fiche d'un groupe qui contient
        la liste de ses membres. La valeur par défaut est ``member``.

        Ce paramètre est ignoré si le paramètre ``attr_memberof`` est défini.

    * - ``attr_mail``
      - Chaîne de caractères
      - non
      - Indique le nom de l'attribut dans la fiche de l'utilisateur qui contient
        son adresse email. La valeur par défaut est ``mail``.

    * - ``attr_memberof``
      - Chaîne de caractères
      - non
      - Indique le nom de l'attribut dans la fiche de l'utilisateur qui contient
        les noms distingués des groupes auxquels l'utilisateur appartient.

        Si cet attribut n'est pas défini, alors une recherche sera effectuée
        sur les groupes afin d'identifier ceux auxquels l'utilisateur appartient.

        Par défaut, cet attribut n'est pas défini.

    * - ``attr_uid``
      - Chaîne de caractères
      - non
      - Indique le nom de l'attribut contenant l'identifiant de l'utilisateur.
        Cet attribut sera utilisé pour valider l'existence de l'utilisateur.
        La valeur par défaut est ``uid``.

        Pour les annuaires Active Directory, il est recommandé d'utiliser
        l'attribut ``sAMAccountName`` à la place de la valeur par défaut.

    * - ``binddn``
      - Chaîne de caractères
      - non
      - Nom distingué du compte à utiliser pour se connecter à l'annuaire LDAP.

        Si ce paramètre n'est pas défini :

        *   Si l'authentification externe est basée sur le protocole Kerberos
            et que la délégation du jeton Kerberos a été configurée dans le
            serveur web, alors le jeton Kerberos de l'utilisateur authentifié
            sera utilisé pour établir la connexion à l'annuaire.
        *   Sinon, la connexion se fait en utilisant une connexion anonyme.

        Il est recommandé de définir ce paramètre car les connexions anonymes
        sont généralement interdites ou ne disposent pas forcément de droits
        suffisants pour obtenir les données nécessaires.

    * - ``bindpw``
      - Chaîne de caractères
      - non
      - Mot de passe associé au compte défini dans le paramètre ``binddn``.

        Ce paramètre n'est pris en compte que si ``binddn`` est également
        défini.

    * - ``group_base``
      - Chaîne de caractères
      - oui
      - Nom distingué de la branche de l'annuaire contenant les groupes.

    * - ``group_filter``
      - Chaîne de caractères
      - non
      - Définit un filtre à appliquer pour rechercher un groupe.
        Ce paramètre utilise la syntaxe des filtres définie dans le protocole LDAP.

        La valeur par défaut est ``(objectClass=*)``.

    * - ``group_scope``
      - Chaîne de caractères
      - non
      - Définit la portée de la recherche parmi les groupes.

        Les valeurs possibles sont :

        *   ``base`` : le résultat doit correspondre exactement à la valeur
            du paramètre ``groups_base``.

        *   ``onelevel`` : le résultat doit être tel que le parent de l'entrée
            est la base de recherche définie par le paramètre ``groups_base``.

        *   ``subordinate`` : le résultat est un descendant de la base de recherche
            définie par le paramètre ``groups_base`` (sans restriction de profondeur),
            mais il ne peut pas s'agir de la base de recherche elle-même.

        *   ``subtree`` : le résultat correspond à la base de recherche définie
            par le paramètre ``groups_base`` ou à l'un de ses descendants
            (sans restriction de profondeur).

        La valeur par défaut est ``subtree``.

    * - ``ldap_deref``
      - Chaîne de caractères
      - non
      - Spécifie le traitement appliqué aux références LDAP.

        Les valeurs possibles sont :

        *   ``always`` : les références sont systématiquement déréférencées.

        *   ``finding`` : seules les références qui concernent le point
            de départ des recherches sont déréférencées.

        *   ``never`` : les références ne sont jamais déréférencées.

        *   ``searching`` : seules les références qui concernent des entrées
            sous le point de départ des recherches sont déréférencées.

        La valeur par défaut est ``never``.

    * - ``ldap_url``
      - Chaîne de caractères
      - oui
      - Définit l'URL de connexion à l'annuaire LDAP.
        Le schéma doit être ``ldap://`` ou ``ldaps://``.

    * - ``normalize_groups``
      - Booléen
      - non
      - Indique si le nom des groupes doit être normalisé (converti en minuscules)
        lors de leur import dans Vigilo ou non.

        Ce paramètre est nécessaire pour contourner les limitations de certaines
        implémentations d'annuaires LDAP. Il est actif par défaut.

    * - ``tls_ca_cert``
      - Chaîne de caractères
      - non
      - Indique l'emplacement d'un fichier ou d'un dossier contenant les certificats
        des autorités de confiance. Ce paramètre permet d'authentifier l'annuaire LDAP.

        Le certificat doit être au format X.509 et être encodé en PEM dans le fichier.

    * - ``tls_cert``
      - Chaîne de caractères
      - non
      - Indique l'emplacement du fichier contenant le certificat SSL à présenter
        à l'annuaire LDAP lors de la connexion.

        Le certificat doit être au format X.509 et être encodé en PEM dans le fichier.

    * - ``tls_key``
      - Chaîne de caractères
      - non
      - Indique l'emplacement de la clé privée correspondant au certificat SSL
        défini dans l'option ``tls_cert``.

        La clé privée doit être au format PKCS#1 ou PKCS#8 et être encodée en PEM
        dans le fichier.

    * - ``tls_reqcert``
      - Chaîne de caractères
      - non
      - Influence la validation du certificat X.509 présenté par l'annuaire LDAP.

        Les valeurs possibles sont :

        *   ``never`` : l'annuaire LDAP ne doit pas présenter de certificat.
        *   ``allow`` : l'annuaire LDAP peut présenter un certificat s'il le souhaite.
            Si le serveur ne présente aucun certificat ou si le certificat présenté
            n'est pas valide, l'erreur est ignorée et la connexion continue normalement.
        *   ``try`` : l'annuaire LDAP peut présenter un certificat s'il le souhaite.
            Si le serveur ne présente aucun certificat, la connexion continue normalement.
            Si le certificat présenté n'est pas valide, la connexion échoue.
        *   ``demand`` ou ``hard`` : l'annuaire LDAP doit envoyer un certificat valide.
            Si le serveur ne présente aucun certificat ou si le certificat présenté
            n'est pas valide, la connexion échoue.

    * - ``tls_starttls``
      - Booléen
      - non
      - Active l'extension STARTTLS pour sécuriser la connexion.

        L'extension est désactivée par défaut.

        ..  note::

            L'utilisation du schéma ``ldaps://`` dans l'URL de connexion
            est différente de l'activation de l'extension STARTTLS.

            Dans le premier cas, la connexion utilise un port dédié aux
            connexions chiffrées (636 par défaut). Elle est chiffrée
            dès sa création.

            Dans le second cas, la connexion est d'abord créée en utilisant
            le port dédié aux connexions non chiffrées (389 par défaut),
            puis une commande STARTTLS est envoyée à l'annuaire pour demander
            l'activation du chiffrement.

    * - ``timeout``
      - Entier
      - non
      - Délai d'expiration des opérations qui font intervenir l'annuaire.

        La valeur par défaut est 0, ce qui désactive l'expiration et peut
        entraîner des blocages ou des ralentissements de l'interface web
        en cas d'indisponibilité ou de lenteur de l'annuaire.

    * - ``use``
      - Chaîne de caractères
      - oui
      - Définit le greffon à instancier.

        Utiliser ``vigilo.turbogears.repoze.plugins.mdldapsync2:VigiloLdapSync``.

    * - ``use_dn``
      - Booléen
      - non
      - Indique si la recherche des groupes auxquels l'utilisateur appartient
        doit se faire en utilisant le nom distingué de l'utilisateur
        (p.ex. ``cn=Foo Bar,ou=People,dc=example,dc=com``), ou bien une forme
        raccourcie (p.ex. ``Foo Bar``).

        Ce paramètre est ignorée si le paramètre ``attr_memberof`` est défini.
        Dans le cas contraire, le paramètre est actif par défaut.

        La forme à utiliser dépend du type d'annuaire LDAP et du schéma utilisé
        pour représenter les groupes. Contactez l'administrateur de l'annuaire
        pour connaître la forme applicable.

    * - ``user_base``
      - Chaîne de caractères
      - oui
      - Nom distingué de la branche de l'annuaire contenant les utilisateurs.

    * - ``user_filter``
      - Chaîne de caractères
      - non
      - Définit un filtre à appliquer pour rechercher un utilisateur.
        Ce paramètre utilise la syntaxe des filtres définie dans le protocole LDAP.

        La valeur par défaut est ``(objectClass=*)``.

    * - ``user_scope``
      - Chaîne de caractères
      - non
      - Définit la portée de la recherche parmi les utilisateurs.

        Les valeurs possibles sont :

        *   ``base`` : le résultat doit correspondre exactement à la valeur
            du paramètre ``users_base``.

        *   ``onelevel`` : le résultat doit être tel que le parent de l'entrée
            est la base de recherche définie par le paramètre ``users_base``.

        *   ``subordinate`` : le résultat est un descendant de la base de recherche
            définie par le paramètre ``users_base`` (sans restriction de profondeur),
            mais il ne peut pas s'agir de la base de recherche elle-même.

        *   ``subtree`` : le résultat correspond à la base de recherche définie
            par le paramètre ``users_base`` ou à l'un de ses descendants
            (sans restriction de profondeur).

        La valeur par défaut est ``subtree``.

Une fois l'instance configurée, il est nécessaire de l'ajouter à la liste
des greffons qui fournissent des méta-données sur l'utilisateur, par exemple :

..  sourcecode:: ini

    [mdproviders]
    plugins =
        ldapsync
        vigilo.turbogears.repoze.plugins.mduser:plugin

``ldapsync`` correspond au nom de l'instance du greffon de synchronisation
des informations.

L'opération est à répéter pour chacune des interfaces web qui doivent utiliser
ce mécanisme (VigiAdmin, VigiBoard, VigiGraph, VigiMap).


Annexes
=======

Matrice des permissions associées aux applications
--------------------------------------------------

Le tableau suivant liste les permissions associées à chaque application avec leur rôle.

vigiboard-access
    Autorise l'utilisateur à se connecter à VigiBoard.

vigiboard-update
    Autorise l'utilisateur à mettre à jour des événements dans VigiBoard.

vigiboard-admin
    Autorise l'utilisateur à forcer l'état d'un événement du bac à « OK ».

vigiboard-silence
    Autorise l'utilisateur à consulter et à éditer les règles de mise en
    silence du bac à événements.

vigigraph-access
    Autorise l'utilisateur à se connecter à VigiGraph.

vigimap-access
    Autorise l'utilisateur à se connecter à VigiMap.

vigimap-edit
    Autorise l'utilisateur à accéder au Mode Édition de VigiMap (pour éditer les cartes).

vigimap-admin
    Autorise l'utilisateur à administrer les groupes de cartes.


Matrice des permissions sur les groupes de données
--------------------------------------------------
Vigilo permet, via l'interface VigiAdmin, d'accorder des permissions à un
utilisateur sur un groupe de données. Ces groupes de données peuvent être de
trois types :

- Groupes d'éléments supervisés (hôtes ou services),
- Groupes de cartes,
- Groupes de graphes.

Les accès accordés sont soit en lecture seule, soit en lecture/écriture.
Lorsqu'un accès est donné sur un groupe, il est également donné implicitement à
tous les descendants de ce groupe dans l'arborescence.

La signification de l'accès en lecture/écriture aux données varie selon le type
d'objet et l'interface manipulée. Le tableau suivant précise la signification
de chaque type d'accès, selon le type d'objet sur lequel il est appliqué et
l'interface de Vigilo consultée.

VigiBoard
    L'accès en lecture seule sur un groupe permet de voir les événements se
    rapportant aux hôtes ou aux services de ce groupe.  L'accès en
    lecture/écriture permet en plus de modifier le statut d'acquittement ou le
    ticket associé aux événements concernant des hôtes ou services du groupe
    [#]_.

VigiGraph
    Groupes d'hôtes ou de services : l'accès en lecture seule sur un groupe
    permet de voir les graphes se rapportant aux hôtes de ce groupe. L'accès en
    lecture/écriture confère les mêmes droits.

    Groupes de graphes : l'accès en lecture seule permet de consulter les
    graphes associés à ce groupe. L'accès en lecture/écriture [#]_ confère
    exactement les mêmes droits.

VigiMap
    Groupes d'hôtes ou de services : l'accès en lecture seule permet de voir
    les hôtes et services contenus dans le groupe et apparaissant sur une
    carte. Il permet également d'utiliser les hôtes et services contenus dans
    le groupe lors de la création ou de la modification d'une carte. L'accès en
    lecture/écriture confère les mêmes droits [#]_.

    Groupes de cartes : l'accès en lecture seule sur un groupe de cartes permet
    de consulter les cartes contenues dans ce groupe. L'accès en
    lecture/écriture permet en plus de créer ou de modifier des cartes dans ce
    groupe [#]_.

    Groupes de graphes : L'accès en lecture seule permet de voir les graphes
    associés au groupe lorsqu'ils sont utilisés sur une carte au travers d'un
    lien de type « service ». Il permet également d'utiliser ces graphes lors
    de la création ou de la modification d'une carte, au sein d'un lien de type
    « service ».  L'accès en lecture/écriture confère les mêmes droits [#]_.

.. [#] Pour le moment, l'accès en lecture seule est suffisant pour ça...
.. [#] L'accès en lecture seule ou en lecture/écriture devrait permettre
   de voir les graphes en question.
.. [#] Cette fonctionnalité n'est pas encore implémentée.
.. [#] Pour le moment, l'accès en lecture seule se comporte comme l'accès
   en lecture/écriture.
.. [#] Cette fonctionnalité n'est pas encore implémentée.


Glossaire - Terminologie
------------------------

Ce chapitre recense les différents termes techniques employés dans ce document
et donne une brève définition de chacun de ces termes.


..  include:: glossaire.rst


.. vim: set tw=79 :
