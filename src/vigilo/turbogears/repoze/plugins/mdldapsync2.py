# -*- coding: utf-8 -*-
# Copyright (C) 2006-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce plugin reçoit des informations concernant l'utilisateur depuis
des variables d'environnement et utilise ces variables pour mettre
à jour la base de données Vigilo (synchronisation avec un annuaire).
"""

import os
import ldap
import ldap.sasl as sasl

import transaction
from sqlalchemy.exc import SQLAlchemyError

from vigilo.models.session import DBSession
from vigilo.models.tables import User, UserGroup

from vigilo.common.gettext import translate
_ = translate(__name__)

__all__ = ['VigiloLdapSync']

class VigiloLdapSync(object):
    """
    Une classe qui synchronise les comptes dans la base de données Vigilo
    (utilisateurs et groupes d'utilisateurs) avec un annuaire externe de
    type LDAP.
    """
    ldap = ldap
    sasl = sasl

    def __init__(self,
        ldap_url,
        user_tree,
        group_tree,
        user_filter,
        group_filter,
        ldap_charset='utf-8',
        binddn=None,
        bindpw='',
        attr_cn='cn',
        attr_mail='mail',
        attr_member_cn='cn',
        use_dn=True,
        timeout=0,
        normalize_groups=True):
        """
        Initialise le plugin de synchronisation LDAP.

        @param ldap_url: Liste d'URLs de connexion à l'annuaire LDAP,
            séparées par des espaces. Le greffon tentera de se connecter
            à chacune des URLs dans l'ordre jusqu'à aboutir.
        @type ldap_url: C{basestring}
        @param ldap_base: le DN (Distinguished Name) de l'entrée
            à partir de laquelle effectuer la recherche LDAP.
        @type ldap_base: C{basestring}
        @param filterstr: Filtre appliqué aux résultats de la recherche
            dans l'annuaire. Par défaut, le filtre vaut "(objectClass=*)".
        @type filterstr: C{basestring}
        @param ldap_charset: Encodage des caractères utilisé par l'annuaire.
        @type ldap_charset: C{basestring}
        @param binddn: DN à utiliser pour faire un bind() sur l'annuaire.
            Si omis, une tentative d'authentification Kerberos de l'utilisateur
            a lieu via le protocole GSSAPI.
        @type binddn: C{basestring} or C{None}
        @param bindpw: Mot de passe associé au DN donné par L{binddn}.
        @type bindpw: C{basestring}
        @param attr_cn: Attribut contenant le nom commun (CN) de l'utilisateur.
        @type attr_cn: C{basestring}
        @param attr_mail: Attribut contenant l'email de l'utilisateur.
        @type attr_mail: C{basestring}
        @param attr_member_cn: Attribut des groupes contenant
            la liste des CNs des membres du groupe.
        @type attr_member_cn: C{basestring}
        @param use_dn: Indique si le nom distingué (DN) de l'utilisateur
            doit être utilisé lors de la recherche des groupes ou juste
            son nom commun.
        @type use_dn: C{bool}
        @param timeout: Indique le délai maximum pour les opérations réseau.
            Utiliser la valeur 0 pour désactiver les limites.
        @type timeout: C{int}
        """
        super(VigiloLdapSync, self).__init__()
        self.ldap_url = filter(None, unicode(ldap_url).split(' '))
        self.user_tree = unicode(user_tree)
        self.user_filter = unicode(user_filter)
        self.group_tree = unicode(group_tree)
        self.group_filter = unicode(group_filter)

        if not len(self.ldap_url):
            raise ValueError("ldap_url should contain at least one URL")

        if binddn is None or isinstance(binddn, basestring):
            self.binddn = binddn
        else:
            raise TypeError("binddn must be a string or None")

        if isinstance(bindpw, basestring):
            self.bindpw = bindpw
        else:
            raise TypeError("bindpw must be a string")

        if isinstance(use_dn, bool):
            use_dn = str(use_dn)
        use_dn = unicode(use_dn, 'utf-8', 'replace').lower()
        if use_dn in ('true', 'yes', 'on', '1'):
            use_dn = True
        elif use_dn in ('false', 'no', 'off', '0'):
            use_dn = False
        else:
            raise ValueError('A boolean value was expected for "use_dn"')

        if isinstance(normalize_groups, bool):
            normalize_groups = str(normalize_groups)
        normalize_groups = unicode(normalize_groups, 'utf-8', 'replace').lower()
        if normalize_groups in ('true', 'yes', 'on', '1'):
            normalize_groups = True
        elif normalize_groups in ('false', 'no', 'off', '0'):
            normalize_groups = False
        else:
            raise ValueError('A boolean value was expected for "normalize_groups"')

        self.ldap_charset = unicode(ldap_charset)
        self.attr_cn = attr_cn
        self.attr_mail = attr_mail
        self.attr_member_cn = attr_member_cn
        self.use_dn = use_dn
        self.timeout = max(0, int(timeout)) or self.ldap.NO_LIMIT
        self.normalize_groups = normalize_groups

    # IMetadataProvider
    def add_metadata(self, environ, identity):
        """
        Cette méthode n'ajoute pas de méta-données à proprement parler.
        À la place, elle crée un utilisateur dans la base de données
        si nécessaire, correspondant au contenu de la variable CGI
        C{REMOTE_USER} transmise par Apache.

        Dans le cas d'un identifiant Kerberos ("uid@REALM"), seule
        la partie "uid" est utilisée pour créer le compte.

        Pour cela, cette méthode effectue une requête à un annuaire LDAP.
        Elle génère en outre des groupes d'utilisateurs dans Vigilo
        correspondant aux groupes de l'utilisateur dans LDAP.

        @param environ: Environnement de la requête HTTP
            en cours de traitement.
        @type environ: C{dict}
        @param identity: Identité de l'utilisateur qui tente
            d'accéder à l'application.
        @type identity: C{dict}
        """
        # Si le nom de cette classe apparait dans les tokens,
        # la synchronisation a déjà eu lieu et il n'y a rien à faire.
        # Ce code fonctionne uniquement si on utilise aussi auth_tkt.
        tokens = tuple(identity.get('tokens', ()))
        if self.__class__.__name__ in tokens:
            return

        # On ne synchronise la base que sur l'identité de l'utilisateur
        # provient d'une source d'authentification externe.
        if environ.get('vigilo.external_auth') != True:
            return

        remote_user = identity['repoze.who.userid']
        logger = environ.get('repoze.who.logger')
        logger and logger.info(_('Remote user: %s'), remote_user)
        user = User.by_user_name(remote_user)

        # On récupère les informations concernant l'utilisateur
        # pour alimenter / mettre à jour notre base de données.
        try:
            (user_fullname, user_email, user_groups) = \
                self.retrieve_user_ldap_info(environ, remote_user)
        except:
            logger and logger.exception(_(
                'Exception while contacting LDAP server'))
            return None

        if user_fullname is None:
            user_fullname = remote_user

        if user_groups is None:
            user_groups = []

        # Création de l'utilisateur si nécessaire.
        if user is None:
            user = User(
                user_name=remote_user,
                fullname=user_fullname,
                email=user_email
            )
            try:
                DBSession.add(user)
                DBSession.flush()
                logger and logger.info(_('New user created: %s'), remote_user)
            except SQLAlchemyError:
                transaction.abort()
                logger and logger.exception(
                    _('Exception during user creation'))
                return None

        current_user_groups = user.usergroups

        # Suppression des groupes présents qui ne devraient plus l'être.
        for group in current_user_groups:
            if not group.group_name in user_groups:
                logger and logger.info(
                    _('Removing user "%(user)s" from group "%(group)s"'),
                    {
                        'user': remote_user,
                        'group': group.group_name,
                    })
                user.usergroups.remove(group)

        # Ajout des groupes manquants.
        for group_name in user_groups:
            try:
                # Cet appel provoque un flush implicite à la 2ème
                # itération, d'où le bloc try...except (cf. #909).
                group = UserGroup.by_group_name(group_name)
            except SQLAlchemyError:
                # Si une erreur s'est produite, on effectue un ROLLBACK
                # pour éviter de bloquer le thread avec l'erreur, mais
                # on continue tout de même car l'utilisateur a bien été
                # reconnu.
                transaction.abort()
                return

            # Création des groupes au besoin.
            if group is None:
                logger and logger.info(
                    _('Creating group "%s"'), group_name)
                group = UserGroup(group_name=group_name)
                DBSession.add(group)

            elif group in current_user_groups:
                continue

            logger and logger.info(
                _('Adding user "%(user)s" to group "%(group)s"'),
                {
                    'user': remote_user,
                    'group': group_name,
                })
            user.usergroups.append(group)

        try:
            DBSession.flush()
            # Nécessaire afin que les modifications soient sauvegardées
            # en base de données. Sans cela, le groupe serait supprimé
            # automatiquement (via un ROLLBACK) en cas d'erreur issue
            # de l'application (status HTTP != 200).
            transaction.commit()
            transaction.begin()
        except SQLAlchemyError:
            transaction.abort()
            logger and logger.exception(_(
                'Exception during groups creation'))
            return None

        # On tente de se souvenir du fait qu'on a déjà synchronisé
        # cet utilisateur en mémorisant le nom de cette classe.
        identity['tokens'] = tokens + (self.__class__.__name__, )

    def connect(self, environ):
        """
        Ouvre la connexion au serveur LDAP.

        Les différentes URLs fournies dans la configuration sont testées
        (par ordre d'apparition dans la liste) jusqu'à ce que la connexion
        soit établie ou jusqu'à épuisement des possibilités.
        Une exception de type C{ldap.SERVER_DOWN} si chacune des tentatives
        de connexion échoue.

        @param environ: Environnement WSGI de la requête.
        @type environ: C{dict}
        @return: Connexion au serveur LDAP.
        @rtype: C{LDAPObject}
        """
        logger = environ.get('repoze.who.logger')
        for ldap_url in self.ldap_url:
            try:
                # Connexion à l'annuaire LDAP
                logger and logger.debug(_('Attempting connection to "%s"'),
                                        ldap_url)
                ldap_conn = self.ldap.initialize(ldap_url)
                ldap_conn.set_option(self.ldap.OPT_NETWORK_TIMEOUT, self.timeout)
                ldap_conn.set_option(self.ldap.OPT_TIMEOUT, self.timeout)
                ldap_conn.set_option(self.ldap.OPT_TIMELIMIT, self.timeout)

                # Si un utilisateur particulier a été configuré pour le bind,
                # on l'utilise.
                if self.binddn:
                    # Les .encode() sont nécessaires car python-ldap ne supporte
                    # pas l'utilisation du type natif "unicode" dans son API.
                    ldap_conn.bind_s(
                        self.binddn.encode('utf-8'),
                        self.bindpw.encode('utf-8'),
                        self.ldap.AUTH_SIMPLE
                    )
                # Sinon on tente plutôt une authentification par Kerberos.
                else:
                    if 'KRB5CCNAME' in environ:
                        os.environ['KRB5CCNAME'] = environ['KRB5CCNAME']
                        auth_tokens = self.sasl.gssapi()
                        ldap_conn.sasl_interactive_bind_s("", auth_tokens)
                    else:
                        ldap_conn.simple_bind()
                return ldap_conn
            except self.ldap.LDAPError:
                logger and logger.exception(
                    _("Could not connect to LDAP server '%s', "
                      "trying next server") % ldap_url)
                continue

        # On a épuisé toutes les URLs sans parvenir à se connecter.
        msg = _("No more LDAP servers to try")
        logger and logger.error(msg)
        raise self.ldap.SERVER_DOWN(msg)

    def retrieve_user_ldap_info(self, environ, login):
        """
        Récupère dans l'annuaire LDAP les informations suivantes :
         - le nom complet de l'utilisateur ;
         - son adresse email ;
         - la liste des groupes auquels il appartient.

        @param login: Login LDAP de l'utilisateur.
        @type login: C{basestring}

        @return: Un tuple contenant ces trois informations
            ou None si la connexion n'a pas pu être établie
            avec l'annuaire LDAP.
        @rtype: C{tuple} of C{mixed} or C{None}
        """
        logger = environ.get('repoze.who.logger')
        user_attributes = {}
        group_attributes = []

        ldap_conn = self.connect(environ)
        try:
            try:
                logger and logger.debug(
                    _("Bound to the LDAP server as '%s'"),
                    ldap_conn.whoami_s()
                )
            except self.ldap.LDAPError:
                # 389 Directory Server (l'annuaire LDAP RedHat)
                # ne supporte pas l'extension "Who am I?".
                pass

            try:
                filter = self.user_filter % login
            except TypeError as e:
                if unicode(e) != u'not all arguments converted ' \
                                 u'during string formatting':
                    raise
                filter = self.user_filter

            # Récupération des informations de l'utilisateur
            user_attributes = ldap_conn.search_s(
                self.user_tree.encode('utf-8'),
                self.ldap.SCOPE_SUBTREE,
                filter.encode('utf-8'),
                attrlist=[
                    self.attr_cn,
                    self.attr_mail,
                ],
            )
            if not user_attributes or not user_attributes[0]:
                raise ValueError(_('User "%s" not found in the LDAP server'),
                                    login)

            try:
                filter = self.group_filter % (self.use_dn and
                                              user_attributes[0][0].decode(self.ldap_charset) or
                                              login)
            except TypeError as e:
                if unicode(e) != u'not all arguments converted ' \
                                 u'during string formatting':
                    raise
                filter = self.group_filter

            user_attributes = user_attributes[0][1]

            # Récupération des groupes de l'utilisateur
            group_attributes = ldap_conn.search_s(
                self.group_tree.encode('utf-8'),
                self.ldap.SCOPE_SUBTREE,
                filter.encode('utf-8'),
                attrlist=[
                    self.attr_member_cn,
                ],
            )
            if not group_attributes or not group_attributes[0]:
                raise ValueError(_('Could not retrieve groups from LDAP server for "%s"'),
                                    login)
        finally:
            # Déconnexion de l'annuaire
            ldap_conn.unbind()

        # Traitement des informations récupérées :
        # - nom complet de l'utilisateur ;
        if user_attributes.has_key(self.attr_cn):
            user_fullname = \
                user_attributes[self.attr_cn][0].decode(self.ldap_charset)
        else:
            user_fullname = None

        # - email de l'utilisateur ;
        if user_attributes.has_key(self.attr_mail):
            user_email = user_attributes[self.attr_mail][0].decode(
                self.ldap_charset)
        else:
            user_email = None

        # - groupes dont fait partie l'utilisateur.
        user_groups = []
        for group_attribute in group_attributes:
            try:
                group = group_attribute[1][self.attr_member_cn][0].decode(
                    self.ldap_charset).strip()
                if self.normalize_groups:
                    group = group.lower()
                user_groups.append(group)
            except (IndexError, TypeError):
                # Certains annuaires (ex: Active Directory) envoient des
                # références dans leurs résultats qui ont un format différent:
                # (None, ['ldap://ForestDnsZones.hst/ =ForestDnsZones,DC=hst'])
                #
                # Ces références lèvent une exception TypeError lorsqu'on y
                # accède comme s'il s'agissait de résultats standards.
                #
                # cf. https://mail.python.org/pipermail/python-ldap/
                #       2005q2/001616.html
                pass

        # On retourne un tuple contenant ces trois informations :
        return (user_fullname, user_email, user_groups)
