%define module  @SHORT_NAME@

Name:       vigilo-%{module}
Summary:    @SUMMARY@
Version:    @VERSION@
Release:    @RELEASE@%{?dist}
Source0:    %{name}-%{version}.tar.gz
URL:        @URL@
Group:      Applications/System
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2
Buildarch:  noarch

BuildRequires:   python-distribute

Requires:   python-distribute
Requires:   vigilo-models vigilo-themes
Requires:   TurboGears2 >= 2.3.1
Requires:   python-toscawidgets
Requires:   python-paste
Requires:   python-paste-deploy
Requires:   python-tw-forms
Requires:   python-decorator >= 3.1.2
Requires:   python-genshi >= 0.5.1
Requires:   python-webflash >= 0.1-0.1.a8
Requires:   python-toscawidgets >= 0.9.4
Requires:   python-weberror >= 0.10.1
Requires:   python-webhelpers >= 1.0-0.2.b7
Requires:   python-repoze-tm2 >= 1.0-0.1.a4
Requires:   python-kerberos python-urllib2-kerberos
Requires:   python-ldap
Requires:   python-transaction
Requires:   python-repoze-who >= 2.1
Requires:   python-zope-interface >= 4.0.0
Requires:   python-tgext-crud >= 0.8.2
Requires:   python-formencode >= 1.3.1
Requires:   python-weberror >= 0.10.3
Requires:   python-repoze-who-friendlyform
Requires:   mod_wsgi
Requires:   findutils


%description
@DESCRIPTION@
This library is part of the Vigilo Project <http://vigilo-project.org>

%prep
%setup -q

%build
make PYTHON=%{__python}

%install
rm -rf $RPM_BUILD_ROOT
make install_pkg \
    DESTDIR=$RPM_BUILD_ROOT \
    PREFIX=%{_prefix} \
    LOCALSTATEDIR=%{_localstatedir} \
    PYTHON=%{__python}

%find_lang %{name}


%clean
rm -rf $RPM_BUILD_ROOT


%files -f %{name}.lang
%defattr(644,root,root,755)
%doc COPYING.txt
%{python_sitelib}/vigilo
%{python_sitelib}/*.egg-info
%{python_sitelib}/*-nspkg.pth
%attr(755,root,root) %{_sysconfdir}/cron.daily/*
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}


%changelog
* Fri Jan 21 2011 Vincent Quéméner <vincent.quemener@c-s.fr>
- Rebuild for RHEL6.

* Tue Aug 24 2010  BURGUIERE Thomas <thomas.burguiere@c-s.fr>
- modification for traduction files

* Mon Feb 08 2010 Aurelien Bompard <aurelien.bompard@c-s.fr>
- initial package
