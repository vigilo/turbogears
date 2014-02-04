# -*- coding: utf-8 -*-
# Copyright (C) 2006-2014 CS-SI
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
        ldap_base,
        filterstr='(objectClass=*)',
        ldap_charset='utf-8',
        http_charset='utf-8',
        cache_name=None,
        binddn=None,
        bindpw=None,
        attr_cn='cn',
        attr_mail='mail',
        attr_member_of='memberOf'):
        """
        Initialise le plugin de synchronisation LDAP.

        @param ldap_url: L'url de connexion à l'annuaire LDAP.
        @type ldap_url: C{basestring}
        @param ldap_base: le DN (Distinguished Name) de l'entrée
            à partir de laquelle effectuer la recherche LDAP.
        @type ldap_base: C{basestring}
        @param filterstr: Filtre appliqué aux résultats de la recherche
            dans l'annuaire. Par défaut, le filtre vaut "(objectClass=*)".
        @type filterstr: C{basestring}
        @param ldap_charset: Encodage des caractères utilisé par l'annuaire.
        @type ldap_charset: C{basestring}
        @param http_charset: Encodage du C{REMOTE_USER} retourné par Apache.
        @type http_charset: C{basestring}
        @type cache_name: C{basestring}
        @param binddn: DN à utiliser pour faire un bind() sur l'annuaire.
            Si omis, une tentative d'authentification Kerberos de l'utilisateur
            a lieu via le protocole GSSAPI.
        @type binddn: C{basestring} or C{None}
        @param bindpw: Mot de passe associé au DN donné par L{binddn}.
        @type bindpw: C{basestring} or C{None}
        """
        super(VigiloLdapSync, self).__init__()
        self.ldap_url = unicode(ldap_url)
        self.ldap_base = unicode(ldap_base)

        if binddn is None or isinstance(binddn, basestring):
            self.binddn = binddn
        else:
            raise TypeError, "binddn must be a string or None"

        if bindpw is None or isinstance(bindpw, basestring):
            self.bindpw = bindpw
        else:
            raise TypeError, "bindpw must be a string or None"

        if cache_name is None or not cache_name.strip():
            self.cache_name = None
        elif isinstance(cache_name, basestring):
            self.cache_name = cache_name
        else:
            raise TypeError, "cache_name must be a string or None"

        self.filterstr = unicode(filterstr)
        self.ldap_charset = unicode(ldap_charset)
        self.http_charset = unicode(http_charset)
        self.attr_cn = attr_cn
        self.attr_mail = attr_mail
        self.attr_member_of = attr_member_of

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

        Ces informations sont synchronisées à chaque requête HTTP
        ou bien une seule fois par session si un cache est utilisé
        (pour plus d'information, voir le paramètre C{cache_name} de
        L{VigiloLdapSync.__init__}).

        @param environ: Environnement de la requête HTTP
            en cours de traitement.
        @type environ: C{dict}
        @param identity: Identité de l'utilisateur qui tente
            d'accéder à l'application.
        @type identity: C{dict}
        """
        if 'REMOTE_USER' not in environ:
            return

        remote_user = environ['REMOTE_USER'].decode(self.http_charset)
        logger = environ.get('repoze.who.logger')
        logger and logger.info(_('Remote user: %s'), remote_user)

        # Une identité Kerberos correspond à un "principal"
        # de la forme "uid@realm". On ne garde que l'uid.
        if '@' in remote_user:
            remote_user = remote_user.split('@', 1)[0]

            # On corrige l'identité trouvée par repoze.who afin que
            # les autres mdproviders puissent trouver une correspondance
            # dans la base de données.
            identity['repoze.who.userid'] = remote_user

        remote_user = unicode(remote_user)
        user = User.by_user_name(remote_user)

        if self.cache_name is not None:
            if 'beaker.session' not in environ:
                logger and logger.warning(
                    _('Beaker must be present in the WSGI middleware '
                    'stack for the cache to work'))
            # L'identité dans le cache doit être la même que celle
            # pour laquelle on est en train de s'authentifier.
            elif self.cache_name in environ['beaker.session'] and \
                environ['beaker.session'][self.cache_name] == remote_user:
                return

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
                if 'beaker.session' in environ and self.cache_name is not None:
                    environ['beaker.session'][self.cache_name] = remote_user
                    environ['beaker.session'].save()
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

        if 'beaker.session' in environ and self.cache_name is not None:
            environ['beaker.session'][self.cache_name] = remote_user
            environ['beaker.session'].save()
        return

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

        # Connexion à l'annuaire LDAP
        try:
            ldap_conn = self.ldap.initialize(self.ldap_url)
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
                filterstr = self.filterstr % login
            except TypeError, e:
                if unicode(e) != u'not all arguments converted ' \
                                 u'during string formatting':
                    raise
                filterstr = self.filterstr

            # Récupération des informations de l'utilisateur
            user_attributes = ldap_conn.search_s(
                self.ldap_base.encode('utf-8'),
                self.ldap.SCOPE_SUBTREE,
                filterstr.encode('utf-8'),
                attrlist=[
                    self.attr_cn,
                    self.attr_mail,
                    self.attr_member_of
                ],
            )
            if not user_attributes or not user_attributes[0]:
                raise ValueError(_('User "%s" not found in the LDAP server'),
                                    login)
            user_attributes = user_attributes[0][1]
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
                self.ldap_charset).lower()
        else:
            user_email = None

        # - groupes dont fait partie l'utilisateur.
        if user_attributes.has_key(self.attr_member_of):
            user_groups = []
            for group in user_attributes[self.attr_member_of]:
                try:
                    group = group.decode(self.ldap_charset
                        ).split(',')[0].split('=')[1].strip().lower()
                except IndexError:
                    pass
                user_groups.append(group)
        else:
            user_groups = None

        # On retourne un tuple contenant ces trois informations :
        return (user_fullname, user_email, user_groups)

    def __repr__(self):
        """Returns a representation of this instance."""
        return '<%s %s>' % (self.__class__.__name__, id(self))
