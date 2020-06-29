# -*- coding: utf-8 -*-
# Copyright (C) 2006-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Ce plugin reçoit des informations concernant l'utilisateur depuis
des variables d'environnement et utilise ces variables pour mettre
à jour la base de données Vigilo (synchronisation avec un annuaire).
"""

import os
import ldap
import ldap.sasl as sasl
from ldap.filter import escape_filter_chars

import transaction
from sqlalchemy.exc import SQLAlchemyError

from vigilo.models.session import DBSession
from vigilo.models.tables import User, UserGroup

from vigilo.common.gettext import translate
_ = translate(__name__)

__all__ = ['VigiloLdapSync']

_CERT_REQ = { "never": ldap.OPT_X_TLS_NEVER,
              "allow": ldap.OPT_X_TLS_ALLOW,
              "demand": ldap.OPT_X_TLS_DEMAND,
              "try": ldap.OPT_X_TLS_TRY,
              "hard": ldap.OPT_X_TLS_HARD,
              "": ldap.OPT_X_TLS_ALLOW,
            }

class VigiloLdapSync(object):
    """
    Une classe qui synchronise les comptes dans la base de données Vigilo
    (utilisateurs et groupes d'utilisateurs) avec un annuaire externe de
    type LDAP.
    """
    ldap = ldap
    sasl = sasl

    @staticmethod
    def _as_bool(optname, optvalue):
        if isinstance(optvalue, bool):
            return optvalue

        optvalue = optvalue.lower()
        if optvalue in ('true', 'yes', 'on', '1'):
            return True
        if optvalue in ('false', 'no', 'off', '0'):
            return False
        raise ValueError('A boolean value was expected for "%s"' % optname)

    def __init__(self,
        ldap_url,
        user_base,
        group_base,
        user_filter='(objectClass=*)',
        group_filter='(objectClass=*)',
        user_scope='subtree',
        group_scope='subtree',
        tls_cert='',
        tls_key='',
        tls_ca_cert='',
        tls_reqcert='',
        tls_starttls=False,
        binddn=None,
        bindpw='',
        attr_uid='uid',
        attr_cn='cn',
        attr_mail='mail',
        attr_memberof='',
        attr_group_cn='cn',
        attr_group_member='member',
        ldap_deref='never',
        use_dn=True,
        normalize_groups=True,
        timeout=0):
        """
        Initialise le plugin de synchronisation LDAP.

        @type ldap_url: C{basestring}
        @param ldap_url: Liste d'URLs de connexion à l'annuaire LDAP,
            séparées par des espaces. Le greffon tentera de se connecter
            à chacune des URLs dans l'ordre jusqu'à aboutir.
        @type user_base: C{basestring}
        @param user_base: la base de recherche pour les utilisateurs.
        @type group_base: C{basestring}
        @param group_base: la base de recherche pour les groupes.
        @type user_filter: C{basestring}
        @param user_filter: Filtre utilisé pour rechercher les utilisateurs.
        @type group_filter: C{basestring}
        @param group_filter: Filtre utilisé pour rechercher les groupes.
        @param user_scope: Spécifie la portée des recherches d'utilisateurs.
            Les valeurs possibles sont "base", "onelevel", "subordinate"
            et "subtree".
        @type user_scope: C{basestring}
        @param group_scope: Spécifie la portée des recherches de groupes.
            Les valeurs possibles sont "base", "onelevel", "subordinate"
            et "subtree".
        @type group_scope: C{basestring}
        @type tls_key: C{basestring}
        @param tls_key: la clé du certificat TLS.
        @type tls_cert: C{basestring}
        @param tls_cert: le certificat TLS.
        @type tls_ca_cert: C{basestring}
        @param tls_ca_cert: la CA du certificat TLS.
        @type tls_reqcert: C{basestring}
        @param tls_reqcert: Option TLS_REQUIRE_CERT (options possibles : never,
            allow, try, demand, hard).
        @type tls_starttls: C{bool}
        @param tls_starttls: Lorsque cette option est active, Vigilo exécute
            la commande STARTTLS juste après la connexion afin de la sécuriser.
        @type binddn: C{basestring} or C{None}
        @param binddn: DN à utiliser pour faire un bind() sur l'annuaire.
            Si omis, une tentative d'authentification Kerberos de l'utilisateur
            a lieu via le protocole GSSAPI.
        @type bindpw: C{basestring}
        @param bindpw: Mot de passe associé au DN donné par L{binddn}.
        @type attr_cn: C{basestring}
        @param attr_cn: Attribut contenant le nom commun (CN) de l'utilisateur.
        @type attr_mail: C{basestring}
        @param attr_mail: Attribut contenant l'email de l'utilisateur.
        @type attr_member_cn: C{basestring}
        @param attr_member_cn: Attribut des groupes contenant
            la liste des CNs des membres du groupe.
        @type attr_member_of: C{basestring}
        @param attr_member_of: Attribut de l'utilisateur contenant
            la liste des groupes dont il est membre.
        @type ldap_deref: C{basestring}
        @param ldap_deref: Indique comment les références qui apparaissent
            dans les résultats doivent être traitées.
            Les valeurs possibles sont "always", "finding", "never"
            et "searching".
        @type use_dn: C{bool}
        @param use_dn: Lorsque cette option est active, le nom distingué (DN)
            de l'utilisateur est utilisé lors de la recherche des groupes.
            Dans le cas contraire, le nom commun (CN) de l'utilisateur est
            utilisé à la place.
        @type normalize_groups: C{bool}
        @param normalize_groups: Lorsque cette option est active, les noms
            des groupes sont normalisés (convertis en minuscules) lorsqu'ils
            sont importés dans Vigilo.
        @type timeout: C{int}
        @param timeout: Indique le délai maximum pour les opérations réseau.
            Utiliser la valeur 0 pour désactiver les limites.
        """
        super(VigiloLdapSync, self).__init__()
        self.ldap_url = filter(None, ldap_url.split(' '))
        self.user_base = user_base
        self.user_filter = user_filter
        self.group_base = group_base
        self.group_filter = group_filter

        if not len(self.ldap_url):
            raise ValueError("ldap_url should contain at least one URL")

        if not isinstance(tls_key, basestring):
            raise TypeError("tls_key must be a string")
        self.tls_key = tls_key

        if not isinstance(tls_cert, basestring):
            raise TypeError("tls_cert must be a string")
        self.tls_cert = tls_cert

        if not isinstance(tls_ca_cert, basestring):
            raise TypeError("tls_ca_cert must be a string ")
        self.tls_ca_cert = tls_ca_cert

        self.tls_reqcert = _CERT_REQ.get(tls_reqcert.lower())
        if self.tls_reqcert is None:
            raise TypeError("tls_reqcert must be one of: %s" % ", ".join(_CERT_REQ.keys()))

        if binddn is None or isinstance(binddn, basestring):
            self.binddn = binddn
        else:
            raise TypeError("binddn must be a string or None")

        if isinstance(bindpw, basestring):
            self.bindpw = bindpw
        else:
            raise TypeError("bindpw must be a string")

        self.user_scope = getattr(ldap, 'SCOPE_' + user_scope.upper(), None)
        if self.user_scope is None:
            raise ValueError('Invalid value for "user_scope": %s')

        self.group_scope = getattr(ldap, 'SCOPE_' + group_scope.upper(), None)
        if self.group_scope is None:
            raise ValueError('Invalid value for "group_scope"')

        self.ldap_deref = getattr(ldap, 'DEREF_' + ldap_deref.upper(), None)
        if self.ldap_deref is None:
            raise ValueError('Invalid value for "ldap_deref"')

        self.use_dn = self._as_bool("use_dn", use_dn)
        self.normalize_groups = self._as_bool("normalize_groups", normalize_groups)
        self.tls_starttls = self._as_bool("tls_starttls", tls_starttls)

        self.attr_uid = attr_uid
        self.attr_cn = attr_cn
        self.attr_mail = attr_mail
        self.attr_memberof = attr_memberof
        self.attr_group_cn = attr_group_cn
        self.attr_group_member = attr_group_member
        self.timeout = max(0, int(timeout)) or ldap.NO_LIMIT

    # IAuthenticator
    def authenticate(self, environ, identity):
        if 'login' not in identity or 'password' not in identity:
            return None

        logger = environ.get('repoze.who.logger')
        ldap_conn = self.connect(environ)
        try:
            # Recherche de l'utilisateur correspondant au login saisi.
            user = ldap_conn.search_s(
                self.user_base,
                self.user_scope,
                '(&%s(%s=%s))' % (
                    self.user_filter,
                    escape_filter_chars(self.attr_uid, 1),
                    escape_filter_chars(identity['login'].encode('utf-8'), 1),
                ),
                [],
            )

            # Aucun résultat ou alors le résultat est une référence
            if not user or not user[0] or not user[0][0]:
                return None

            # Tentative de reconnexion en utilisant le DN trouvé
            # et le mot de passe associé.
            # Une exception ldap.LDAPError est levée en cas d'échec.
            ldap_conn.simple_bind_s(user[0][0], identity['password'])

            # Permet la synchronisation des groupes avec l'annuaire LDAP
            # si le plugin est également déclaré comme "mdprovider".
            identity['tokens'] = identity.get('tokens', ()) + ('external', )

            # Succès de l'authentification.
            return identity['login']
        except Exception as e:
            logger.info(_('Could not authentificate "%(login)s": %(error)s'),
                {'login': identity['login'], 'error': str(e)})
            return None
        finally:
            # Déconnexion propre de l'annuaire
            ldap_conn.unbind()

    # IMetadataProvider
    def add_metadata(self, environ, identity):
        """
        Cette méthode n'ajoute pas de méta-données dans l'identité repoze.

        À la place, elle crée/met à jour la fiche de l'utilisateur authentifié
        dans la base de données, idem pour les groupes d'utilisateurs, puis
        elle met à jour l'association entre les deux.

        Ce plugin ne s'exécute que si le plugin "ExternalIdentification"
        a détecté une identité provenant d'une authentification externe.

        @param environ: Environnement WSGI de la requête.
        @type environ: C{dict}
        @param identity: Identité de l'utilisateur authentifié.
        @type identity: C{dict}
        """
        # Si le nom de cette classe apparait dans les tokens,
        # la synchronisation a déjà eu lieu et il n'y a rien à faire.
        # Ce code fonctionne uniquement si on utilise aussi auth_tkt.
        tokens = tuple(identity.get('tokens', ()))
        if self.__class__.__name__ in tokens:
            return

        # On ne synchronise la base que si l'identité de l'utilisateur
        # provient d'une source d'authentification externe.
        if 'external' not in tokens:
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
                new_ctxt = False
                # Connexion à l'annuaire LDAP
                logger and logger.debug(_('Attempting connection to "%s"'),
                                        ldap_url)
                ldap_conn = self.ldap.initialize(ldap_url)
                ldap_conn.set_option(ldap.OPT_NETWORK_TIMEOUT, self.timeout)
                ldap_conn.set_option(ldap.OPT_TIMEOUT, self.timeout)
                ldap_conn.set_option(ldap.OPT_TIMELIMIT, self.timeout)
                ldap_conn.set_option(ldap.OPT_DEREF, self.ldap_deref)

                if self.tls_key:
                    ldap_conn.set_option(ldap.OPT_X_TLS_KEYFILE, self.tls_key)
                    new_ctxt = True

                if self.tls_cert:
                    ldap_conn.set_option(ldap.OPT_X_TLS_CERTFILE, self.tls_cert)
                    new_ctxt = True

                if self.tls_ca_cert:
                    ldap_conn.set_option(ldap.OPT_X_TLS_CACERTFILE, self.tls_ca_cert)
                    new_ctxt = True

                if self.tls_reqcert:
                    ldap_conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, self.tls_reqcert)
                    new_ctxt = True

                # Si une des options TLS est positionnée alors on force la création
                # d'un nouveau contexte pour la connexion TLS
                if new_ctxt or self.tls_starttls:
                    ldap_conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

                if self.tls_starttls:
                    ldap_conn.start_tls_s()

                # Si un utilisateur particulier a été configuré pour le bind,
                # on l'utilise.
                if self.binddn:
                    # Les .encode() sont nécessaires car python-ldap ne supporte
                    # pas l'utilisation du type natif "unicode" dans son API.
                    ldap_conn.bind_s(
                        self.binddn.encode('utf-8'),
                        self.bindpw.encode('utf-8'),
                        ldap.AUTH_SIMPLE
                    )
                # Sinon on tente plutôt une authentification par Kerberos.
                else:
                    if 'KRB5CCNAME' in environ:
                        os.environ['KRB5CCNAME'] = environ['KRB5CCNAME']
                        auth_tokens = self.sasl.gssapi()
                        ldap_conn.sasl_interactive_bind_s("", auth_tokens)
                    else:
                        ldap_conn.simple_bind()

                try:
                    logger and logger.debug(
                        _("Bound to the LDAP server as '%s'"),
                        ldap_conn.whoami_s()
                    )
                except ldap.LDAPError:
                    # 389 Directory Server (l'annuaire LDAP RedHat)
                    # ne supporte pas l'extension "Who am I?".
                    pass

                return ldap_conn
            except ldap.LDAPError:
                logger and logger.exception(
                    _("Could not connect to LDAP server '%s', "
                      "trying next server") % ldap_url)
                continue

        # On a épuisé toutes les URLs sans parvenir à se connecter.
        msg = _("No more LDAP servers to try")
        logger and logger.error(msg)
        raise ldap.SERVER_DOWN(msg)

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
        ldap_conn = self.connect(environ)
        try:
            filt = '(&%s(%s=%s))' % (
                self.user_filter,
                escape_filter_chars(self.attr_uid, 1),
                escape_filter_chars(login.encode('utf-8'), 1),
            )

            # Récupération des informations de l'utilisateur
            attrlist = [
                self.attr_cn,
                self.attr_mail,
            ]
            # Si possible, on récupère les DN des groupes en même temps.
            if self.attr_memberof:
                attrlist.append(self.attr_memberof)

            user_attributes = ldap_conn.search_s(
                self.user_base,
                self.user_scope,
                filt,
                attrlist,
            )
            if not user_attributes or not user_attributes[0]:
                raise ValueError(_('User "%s" not found in the LDAP server'), login)

            if self.attr_memberof:
                # Récupération des CNs des groupes en utilisant les DNs
                # contenus dans l'attribut memberOf de l'utilisateur.
                group_attributes = []
                if self.attr_memberof in user_attributes[0][1]:
                    for group in user_attributes[0][1][self.attr_memberof]:
                        group_attributes.extend(ldap_conn.search_s(
                            group,
                            # On a un DN, donc seul SCOPE_BASE a du sens ici.
                            ldap.SCOPE_BASE,
                            self.group_filter,
                            attrlist=[self.attr_group_cn],
                        ))
            else:
                # Récupération des CNs des groupes en recherchant via
                # l'attribut member des groupes.
                filt = '(&%s(%s=%s))' % (
                    self.group_filter,
                    escape_filter_chars(self.attr_group_member, 1),
                    escape_filter_chars(
                        user_attributes[0][0]
                        if self.use_dn
                        else login.encode('utf-8'),
                        1
                    ),
                )
                group_attributes = ldap_conn.search_s(
                    self.group_base,
                    self.group_scope,
                    filt,
                    attrlist=[self.attr_group_cn],
                )
        finally:
            # Déconnexion de l'annuaire
            ldap_conn.unbind()

        # Résultats de la requête concernant l'utilisateur.
        user_attributes = user_attributes[0][1]

        # Traitement des informations récupérées :
        # - nom complet de l'utilisateur ;
        if self.attr_cn in user_attributes:
            user_fullname = user_attributes[self.attr_cn][0].decode('utf-8')
        else:
            user_fullname = None

        # - email de l'utilisateur ;
        if self.attr_mail in user_attributes:
            user_email = user_attributes[self.attr_mail][0].decode('utf-8')
        else:
            user_email = None

        # - groupes dont fait partie l'utilisateur.
        user_groups = []
        for group_attribute in group_attributes:
            # group_attribute[0] vaut None lorsque l'annuaire répond avec
            # une référence (p.ex. Active Directory) :
            #
            # (None, ['ldap://ForestDnsZones.hst/ =ForestDnsZones,DC=hst'])
            #
            # cf. https://mail.python.org/pipermail/python-ldap/2005q2/001616.html
            if group_attribute[0] is None or self.attr_group_cn not in group_attribute[1]:
                continue

            group = group_attribute[1][self.attr_group_cn][0].decode('utf-8')
            if self.normalize_groups:
                group = group.lower()
            user_groups.append(group)

        # On retourne un tuple contenant ces trois informations :
        return (user_fullname, user_email, user_groups)
