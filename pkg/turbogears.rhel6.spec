%define module  turbogears
%define name    vigilo-%{module}
%define version 2.0.0
%define release 1%{?svn}%{?dist}

Name:       %{name}
Summary:    Vigilo Turbogears extension library
Version:    %{version}
Release:    %{release}
Source0:    %{name}-%{version}.tar.gz
URL:        http://www.projet-vigilo.org
Group:      System/Servers
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2
Buildarch:  noarch

BuildRequires:   python-distribute

Requires:   python-distribute
Requires:   vigilo-models vigilo-themes
Requires:   python-repoze-what-quickstart
Requires:   python-tg-devtools
Requires:   python-turbogears2
Requires:   python-toscawidgets
Requires:   python-paste
Requires:   python-paste-deploy
Requires:   python-tw-forms
Requires:   python-rum >= 0.3
Requires:   python-rum < 0.4
Requires:   python-tgrum
Requires:   python-rumalchemy
Requires:   python-tw-rum
Requires:   python-decorator >= 3.1.2
Requires:   python-pylons >= 0.9.7
Requires:   python-genshi >= 0.5.1
Requires:   python-webflash >= 0.1-0.1.a8
Requires:   python-toscawidgets >= 0.9.4
Requires:   python-weberror >= 0.10.1
Requires:   python-repoze-what-pylons
Requires:   python-repoze-tm2 >= 1.0-0.1.a4
Requires:   python-turbojson >= 1.2.1
Requires:   python-kerberos python-urllib2-kerberos
Requires:   python-rum-policy python-rum-component python-rum-generic


%description
This library provides the Vigilo extensions to TurboGears 2
This library is part of the Vigilo Project <http://vigilo-project.org>

%prep
%setup -q

%build
make PYTHON=%{__python}

%install
rm -rf $RPM_BUILD_ROOT
make install \
    DESTDIR=$RPM_BUILD_ROOT \
    PYTHON=%{__python}

%find_lang %{name}


%clean
rm -rf $RPM_BUILD_ROOT


%files -f %{name}.lang
%defattr(644,root,root,755)
%doc COPYING
%{python_sitelib}/vigilo
%{python_sitelib}/*.egg-info
%{python_sitelib}/*-nspkg.pth


%changelog
* Fri Jan 21 2011 Vincent Quéméner <vincent.quemener@c-s.fr> - 1.0-3
- Rebuild for RHEL6.

* Tue Aug 24 2010  BURGUIERE Thomas <thomas.burguiere@c-s.fr> - 1.0-2
- modification for traduction files

* Mon Feb 08 2010 Aurelien Bompard <aurelien.bompard@c-s.fr> - 1.0-1
- initial package