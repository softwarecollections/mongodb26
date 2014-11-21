%{!?scl_name_base:%global scl_name_base mongodb}
%{!?scl_name_version:%global scl_name_version 26}
# particularly useful for mock
%{!?scl:%global scl %{scl_name_base}%{scl_name_version}}
%scl_package %scl
# needed, because we can't use Requires: %{?scl_v8_%{scl_name_base}}
%global scl_v8 v8314
%global scl_v8_prefix %{scl_v8}-
# do not produce empty debuginfo package (https://bugzilla.redhat.com/show_bug.cgi?id=1061439#c2)
%global debug_package %{nil}

Summary:	Package that installs %scl
Name:		%scl_name
Version:	2.0
Release:	2%{?dist}
License:	GPLv2+
Group:		Applications/File
Source0:	macros.mongodb26
Source1:	mongodb26-javapackages-provides-wrapper
Source2:	mongodb26-javapackages-requires-wrapper
# template of man page with RPM macros to be expanded
Source3:	README
# mongodb license
Source4:	LICENSE
Requires:	scl-utils
Requires:	%{scl_v8}
Requires:	%{?scl_prefix}mongodb-server
BuildRequires:	scl-utils-build, help2man

%description
This is the main package for %scl Software Collection, which installs
necessary packages to use MongoDB 2.6 server. Software Collections allow
to install more versions of the same package by using alternative
directory structure.
Install this package if you want to use MongoDB 2.6 server on your system

%package runtime
Summary:	Package that handles %scl Software Collection.
Group:		Applications/File
Requires:	scl-utils
Requires:	/usr/bin/scl_source
Requires:	%{scl_v8_prefix}runtime
Requires(post):	policycoreutils-python, libselinux-utils

%description runtime
Package shipping essential scripts to work with %scl Software Collection.

%package build
Summary:	Package shipping basic build configuration
Requires:	%{name}-runtime = %{version}
Requires:	scl-utils-build
Requires:	%{scl_v8_prefix}scldevel
Requires:	%{scl_prefix}scldevel
Group:		Applications/File

%description build
Package shipping essential configuration macros to build
%scl Software Collection.

%package scldevel
Summary:	Package shipping development files for %scl.
Group:		Applications/File

%description scldevel
Development files for %scl (useful e.g. for hierarchical collection
building with transitive dependencies).

%prep
%setup -c -T

%setup -c -T
# java.conf
cat <<EOF >java.conf
# Java configuration file for %{scl} software collection.
JAVA_LIBDIR=%{_javadir}
JNI_LIBDIR=%{_jnidir}
JVM_ROOT=%{_jvmdir}
EOF
# javadoc.req See SOURCE2
cat <<EOF >javadoc.req
#!/bin/sh
# always required for javadocs
# for directory ownership
echo %{name}-runtime
EOF
# XMvn config
cat <<EOF >configuration.xml
<!-- XMvn configuration file for the %{scl} software collection -->
<configuration>
  <resolverSettings>
    <prefixes>
      <prefix>/opt/rh/%{scl}/root</prefix>
    </prefixes>
  </resolverSettings>
  <installerSettings>
    <metadataDir>opt/rh/%{scl}/root/usr/share/maven-fragments</metadataDir>
  </installerSettings>
  <repositories>
    <repository>
      <id>%{scl}-resolve</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-resolve</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>resolve-system</id>
      <type>compound</type>
      <properties>
        <prefix>/</prefix>
      </properties>
      <configuration>
        <repositories>
          <repository>%{scl}-resolve</repository>
          <repository>base-resolve</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>install</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-install</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>install-raw-pom</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-raw-pom</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>install-effective-pom</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-effective-pom</repository>
        </repositories>
      </configuration>
    </repository>
  </repositories>
</configuration>
EOF

cat > README <<\EOF
%{expand:%(cat %{SOURCE3})}
EOF
# copy the license file so %%files section sees it
cp %{SOURCE4} .

%build
# temporary helper script used by help2man
cat > h2m_helper <<\EOF
#!/bin/sh
if [ "$1" = "--version" ]; then
  printf '%%s' "%{scl_name} %{version} Software Collection"
else
  cat README
fi
EOF
chmod a+x h2m_helper
# generate the man page
help2man -N --section 7 ./h2m_helper -o %{scl_name}.7

%install
mkdir -p %{buildroot}%{_scl_scripts}/root
# During the build of this package, we don't know which architecture it is
# going to be used on, so if we build on 64-bit system and use it on 32-bit,
# the %{_libdir} would stay expanded to '.../lib64'. This way we determine
# architecture everytime the 'scl enable ...' is run and set the
# LD_LIBRARY_PATH accordingly
cat >> %{buildroot}%{_scl_scripts}/enable << EOF
export PATH=%{_bindir}\${PATH:+:\${PATH}}
export LIBRARY_PATH=%{_libdir}\${LIBRARY_PATH:+:\${LIBRARY_PATH}}
export LD_LIBRARY_PATH=%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}
export MANPATH=%{_mandir}:\${MANPATH}
export PKG_CONFIG_PATH=%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}
export CPATH=%{_includedir}\${CPATH:+:\${CPATH}}
# Needed by Java Packages Tools to locate java.conf
export JAVACONFDIRS="%{_sysconfdir}/java:\${JAVACONFDIRS:-/etc/java}"
# Required by XMvn to locate its configuration file(s)
export XDG_CONFIG_DIRS="%{_sysconfdir}/xdg:\${XDG_CONFIG_DIRS:-/etc/xdg}"
# Not really needed by anything for now, but kept for consistency with
# XDG_CONFIG_DIRS.
export XDG_DATA_DIRS="%{_datadir}:\${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
. scl_source enable %{scl_v8}
EOF

cat >> %{buildroot}%{_scl_scripts}/service-environment << EOF
# Services are started in a fresh environment without any influence of user's
# environment (like environment variable values). As a consequence,
# information of all enabled collections will be lost during service start up.
# If user needs to run a service under any software collection enabled, this
# collection has to be written into %{scl}_SCLS_ENABLED variable in
# /opt/rh/sclname/service-environment.
$(printf '%%s' '%{scl}' | tr '[:lower:][:space:]' '[:upper:]_')_SCLS_ENABLED='%{scl}'
EOF

install -d -m 755           %{buildroot}%{_sysconfdir}/java
install -p -m 644 java.conf %{buildroot}%{_sysconfdir}/java/

install -d -m 755                   %{buildroot}%{_sysconfdir}/xdg/xmvn
install -p -m 644 configuration.xml %{buildroot}%{_sysconfdir}/xdg/xmvn/

install -d -m 755                   %{buildroot}/opt/rh/%{name}/root/%{_rpmconfigdir}
install -p -m 755 javadoc.req       %{buildroot}/opt/rh/%{name}/root/%{_rpmconfigdir}/javadoc.req

# install magic for java mvn provides/requires generators
install -Dpm0644 %{SOURCE0} %{buildroot}%{_root_sysconfdir}/rpm/macros.%{name}
install -Dpm0755 %{SOURCE1} %{buildroot}%{_rpmconfigdir}/%{name}-javapackages-provides-wrapper
install -Dpm0755 %{SOURCE2} %{buildroot}%{_rpmconfigdir}/%{name}-javapackages-requires-wrapper

# Create java/maven directories so that they'll get properly owned.
# These are listed in the scl_files macro. See also: RHBZ#1057169
install -d -m 755 %{buildroot}%{_javadir}
install -d -m 755 %{buildroot}%{_prefix}/lib/java
install -d -m 755 %{buildroot}%{_javadocdir}
install -d -m 755 %{buildroot}%{_mavenpomdir}
install -d -m 755 %{buildroot}%{_datadir}/maven-effective-poms
install -d -m 755 %{buildroot}%{_mavendepmapfragdir}

# install generated man page
install -d -m 755               %{buildroot}%{_mandir}/man7
install -p -m 644 %{scl_name}.7 %{buildroot}%{_mandir}/man7/

%scl_install

# scldevel garbage
cat >> %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel << EOF
%%scl_%{scl_name_base} %{?scl}
%%scl_prefix_%{scl_name_base} %{?scl_prefix}
EOF

%post runtime
# Simple copy of context from system root to DSC root.
# In case new version needs some additional rules or context definition,
# it needs to be solved.
semanage fcontext -a -e /var/log/mongodb /var/log/%{?scl_prefix}mongodb >/dev/null 2>&1 || :
semanage fcontext -a -e /etc/rc.d/init.d/mongod /etc/rc.d/init.d/%{?scl_prefix}mongod >/dev/null 2>&1 || :
semanage fcontext -a -e /etc/rc.d/init.d/mongod /etc/rc.d/init.d/%{?scl_prefix}mongos >/dev/null 2>&1 || :
semanage fcontext -a -e / %{_scl_root} >/dev/null 2>&1 || :
selinuxenabled && load_policy >/dev/null 2>&1 || :
restorecon -R %{_scl_root} >/dev/null 2>&1 || :
restorecon -R /var/log/%{scl_prefix}mongodb >/dev/null 2>&1 || :
restorecon /etc/rc.d/init.d/%{scl_prefix}mongod >/dev/null 2>&1 || :

%files

%files runtime
%doc README LICENSE
%scl_files
%config(noreplace) %{_scl_scripts}/service-environment
%config(noreplace) %{_sysconfdir}/java/java.conf
%config(noreplace) %{_sysconfdir}/xdg/xmvn/configuration.xml
%{_mandir}/man7/%{scl_name}.*

%files build
%{_root_sysconfdir}/rpm/macros.%{scl}-config
%{_root_sysconfdir}/rpm/macros.%{name}
%{_rpmconfigdir}/%{name}*

%files scldevel
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
* Tue Nov 18 2014 Marek Skalicky <mskalic@redhat.com> 2.0-2
- Changed and cleaned up requirements

* Fri Nov 14 2014 Marek Skalicky <mskalic@redhat.com> 2.0-1
- added SCL v8 dependency
- changed version for SCL 2.0

* Fri Nov 07 2014 Marek Skalicky <mskalic@redhat.com> 1-2
- removed SCL v8 dependency

* Thu Oct 30 2014 Marek Skalicky <mskalic@redhat.com> 1-1
- initial packaging (based on mongodb24 SCL)

