%define module  turbogears
%define name    vigilo-%{module}
%define version 2.0.0
%define release 1%{?svn}

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
Requires:   vigilo-common vigilo-models vigilo-themes
Requires:   python-repoze.tm2
Requires:   python-repoze.what-quickstart
Requires:   python-tg.devtools
Requires:   python-turbogears2
Requires:   python-toscawidgets
Requires:   python-paste
Requires:   python-pastedeploy

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


%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc COPYING
%{python_sitelib}/vigilo
%{python_sitelib}/*.egg-info


%changelog
* Mon Feb 08 2010 Aurelien Bompard <aurelien.bompard@c-s.fr> - 1.0-1
- initial package
