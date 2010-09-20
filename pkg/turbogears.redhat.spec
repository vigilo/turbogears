%define module  turbogears
%define name    vigilo-%{module}
%define version 2.0.0
%define release 1%{?svn}%{?dist}

%define pyver 26
%define pybasever 2.6
%define __python /usr/bin/python%{pybasever}
%define __os_install_post %{__python26_os_install_post}
%{!?python26_sitelib: %define python26_sitelib %(python26 -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:       %{name}
Summary:    Vigilo Turbogears extension library
Version:    %{version}
Release:    %{release}
Source0:    %{module}.tar.bz2
URL:        http://www.projet-vigilo.org
Group:      System/Servers
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2
Buildarch:  noarch

BuildRequires:   python26-distribute

Requires:   python26-distribute
Requires:   vigilo-models vigilo-themes
Requires:   python26-repoze.tm2
Requires:   python26-repoze.what-quickstart
Requires:   python26-tg.devtools
Requires:   python26-turbogears2
Requires:   python26-toscawidgets
Requires:   python26-paste
Requires:   python26-pastedeploy
Requires:   python26-tw.forms
Requires:   python26-rum
Requires:   python26-TgRum
Requires:   python26-RumAlchemy
Requires:   python26-tw.rum
Requires:   python26-decorator >= 3.1.2
Requires:   python26-pylons >= 0.9.7
Requires:   python26-genshi >= 0.5.1
Requires:   python26-webflash >= 0.1a8
Requires:   python26-toscawidgets >= 0.9.4
Requires:   python26-weberror >= 0.10.1
Requires:   python26-repoze.what-pylons 
Requires:   python26-repoze.tm2 >= 1.0a4
Requires:   python26-turbojson >= 1.2.1
Requires:   python26-kerberos python26-urllib2-kerberos


%description
This library provides the Vigilo extensions to TurboGears 2
This library is part of the Vigilo Project <http://vigilo-project.org>

%prep
%setup -q -n %{module}

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
%defattr(-,root,root)
%doc COPYING
%{python26_sitelib}/vigilo
%{python26_sitelib}/*.egg-info
%{python26_sitelib}/*-nspkg.pth


%changelog
* Tue Aug 24 2010  BURGUIERE Thomas <thomas.burguiere@c-s.fr>
- modification for traduction files

* Mon Feb 08 2010 Aurelien Bompard <aurelien.bompard@c-s.fr> - 1.0-1
- initial package

