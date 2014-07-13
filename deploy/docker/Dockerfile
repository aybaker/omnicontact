#------------------------------------------------------------
# Crea container para deployar FTSender
#
# ATENCION! EL CONTAINER GENERADO ES TOTALMENTE INSEGURO
#  ya que el acceso SSH *NO* solicita password.
#
# Contiene:
#  - configuracion de proxy
#  - openssh
#  - EPEL
#
#
# Para crear la imagen:
#  $ docker build --rm=true -t hgdeoro/fts-base .
#
# Para crear el container:
#  $ docker run -i -t hgdeoro/fts-base /bin/bash
#

FROM centos:centos6

MAINTAINER hgdeoro@gmail.com

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV HOME /root
ENV http_proxy http://172.17.42.1:3128
ENV https_proxy http://172.17.42.1:3128
ENV proxy http://172.17.42.1:3128

# Epel
#RUN rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm
RUN rpm -Uvh https://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm

# Repo pgsql
#RUN rpm -Uvh http://yum.postgresql.org/9.3/redhat/rhel-6-i386/pgdg-centos93-9.3-1.noarch.rpm
RUN rpm -Uvh http://yum.postgresql.org/9.3/redhat/rhel-6-x86_64/pgdg-centos93-9.3-1.noarch.rpm

# Instalas paquetes. 1ra linea: basicos. Demas lineas: instalados por Ansible
#  1) '--enablerepo centosplus' workaround p/poder instalar libselinux-python
#       Ver: https://bugs.centos.org/view.php?id=7126
RUN yum --enablerepo centosplus install -y openssh-server sudo passwd supervisor \
	postgresql93 \
	postgresql93-contrib \
	postgresql93-server \
	postgresql93-devel \
	postgresql93-plpython \
	nginx \
	munin \
	munin-node \
	redis \
	sox \
	make \
	get \
	openssl-devel \
	ncurses-devel \
	newt-devel \
	libxml2-devel \
	kernel-devel \
	gcc \
	gcc-c++ \
	sqlite-devel \
	libuuid-devel \
	libselinux-python \
	python-psycopg2 \
	python-virtualenv \
	rsync \
	libxslt-devel \
	python-devel \
	ntp \
	ntpdate

RUN yum groupinstall -y "Development tools"

RUN touch /etc/yum.repos.d/epel.repo /etc/yum.repos.d/pgdg-93-centos.repo

# FIX locales
RUN yum reinstall -y glibc-common

# Setup users
RUN adduser ftsender
RUN passwd --delete root
RUN passwd --delete ftsender

# Setup sudo
RUN echo "ftsender ALL=(ALL)       NOPASSWD: ALL" > /etc/sudoers.d/ftsender

# Setup ssh
RUN echo -e "Protocol 2\nPermitRootLogin yes\nPermitEmptyPasswords yes\nGSSAPIAuthentication no\nUsePAM no" > /etc/ssh/sshd_config

# Seteamos timezone
RUN cp -fv /usr/share/zoneinfo/America/Argentina/Cordoba /etc/localtime

# Genera claves
RUN service sshd start

# Setup supervisord
RUN mkdir -p /etc/supervisor/conf.d /var/log/supervisor/
COPY supervisor.conf /etc/supervisord.conf

EXPOSE 22

CMD ["/usr/bin/supervisord"]

