%define module  turbogears
%define name    vigilo-%{module}
%define version 2.0.0
%define release 1%{?svn}%{?dist}

Name:       %{name}
Summary:    Vigilo Turbogears extension library
Version:    %{version}
Release:    %{release}
Source0:    %{module}.tar.bz2
URL:        http://www.projet-vigilo.org
Group:      System/Servers
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2

BuildRequires:   python-setuptools

Requires:   python >= 2.5
Requires:   python-setuptools
Requires:   vigilo-models vigilo-themes
Requires:   python-repoze.tm2
Requires:   python-repoze.what-quickstart
Requires:   python-tg.devtools
Requires:   python-turbogears2
Requires:   python-toscawidgets
Requires:   python-paste
Requires:   python-pastedeploy
Requires:   python-tw.forms
Requires:   python-rum
Requires:   python-TgRum
Requires:   python-RumAlchemy
Requires:   python-tw.rum
Requires:   python-decorator >= 3.1.2
Requires:   python-pylons >= 0.9.7
Requires:   python-genshi >= 0.5.1
Requires:   python-webflash >= 0.1a8
Requires:   python-toscawidgets >= 0.9.4
Requires:   python-weberror >= 0.10.1
Requires:   python-repoze.what-pylons 
Requires:   python-repoze.tm2 >= 1.0a4
Requires:   python-turbojson >= 1.2.1

Buildarch:  noarch


%description
This library provides the Vigilo extensions to TurboGears 2
This library is part of the Vigilo Project <http://vigilo-project.org>

%prep
%setup -q -n %{module}

%build
make PYTHON=%{_bindir}/python

%install
rm -rf $RPM_BUILD_ROOT
make install \
	DESTDIR=$RPM_BUILD_ROOT \
	PYTHON=%{_bindir}/python

%find_lang %{name}


%clean
rm -rf $RPM_BUILD_ROOT


%files -f %{name}.lang
%defattr(-,root,root)
%doc COPYING
%{python_sitelib}/vigilo
%{python_sitelib}/*.egg-info
%{python_sitelib}/*-nspkg.pth


%changelog
* Tue Aug 24 2010  BURGUIERE Thomas <thomas.burguiere@c-s.fr>
- modification for traduction files

* Mon Feb 08 2010 Aurelien Bompard <aurelien.bompard@c-s.fr> - 1.0-1
- initial package

