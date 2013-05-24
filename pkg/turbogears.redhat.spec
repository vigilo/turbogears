%define module  @SHORT_NAME@

%define pyver 26
%define pybasever 2.6
%define __python /usr/bin/python%{pybasever}
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
# Turn off the brp-python-bytecompile script
%define __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')

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

BuildRequires:   python26-distribute

Requires:   python26-distribute
Requires:   vigilo-models vigilo-themes
Requires:   python26-repoze-what-quickstart
Requires:   python26-tg-devtools
Requires:   python26-turbogears2
Requires:   python26-toscawidgets
Requires:   python26-paste
Requires:   python26-paste-deploy
Requires:   python26-tw-forms
Requires:   python26-rum >= 0.3
Requires:   python26-rum < 0.4
Requires:   python26-tgrum
Requires:   python26-rumalchemy
Requires:   python26-tw-rum
Requires:   python26-decorator3 >= 3.1.2
Requires:   python26-pylons >= 0.9.7
Requires:   python26-genshi >= 0.5.1
Requires:   python26-webflash >= 0.1-0.1.a8
Requires:   python26-toscawidgets >= 0.9.4
Requires:   python26-weberror >= 0.10.1
Requires:   python26-webhelpers >= 1.0-0.2.b7
Requires:   python26-repoze-what-pylons
Requires:   python26-repoze-tm2 >= 1.0-0.1.a4
Requires:   python26-turbojson >= 1.2.1
Requires:   python26-kerberos python26-urllib2-kerberos
Requires:   python26-rum-policy python26-rum-component python26-rum-generic
Requires:   python26-ldap
Requires:   python26-transaction
Requires:   findutils

# Le plugin a été absorbé par vigilo-turbogears 2.0.8.
Obsoletes:  vigilo-repoze.who.plugins.vigilo.kerberos <= 2.0.7
Provides:   vigilo-repoze.who.plugins.vigilo.kerberos = %{version}-%{release}
Conflicts:  vigilo-repoze.who.plugins.vigilo.kerberos <= 2.0.7


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
* Tue Aug 24 2010  BURGUIERE Thomas <thomas.burguiere@c-s.fr>
- updated to include translation files

* Mon Feb 08 2010 Aurelien Bompard <aurelien.bompard@c-s.fr> - 1.0-1
- initial package
