#------------------------------------------------------------
# Crea container para deployar FTSender
#
# ATENCION! EL CONTAINER GENERADO ES TOTALMENTE INSEGURO
#  ya que el acceso SSH *NO* solicita password.
#
# Contiene:
#  - configuracion de proxy
#  - openssh (permite acceso SIN password!)
#  - EPEL
#  - postgresql
#  - instala paquetes basicos
#
# Para crear la imagen:
#  $ docker build --rm=true -t hgdeoro/fts-base .
#
# Para crear y/o lanzar un container:
#  $ docker run -i -t hgdeoro/fts-base /bin/bash
#
# Para lanzar container nuevo en background
#  $ docker run -d -p 9022:22 hgdeoro/fts-base
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

# Evita que Ansible instale repos (ya que instalara repos i386)
RUN touch /etc/yum.repos.d/epel.repo /etc/yum.repos.d/pgdg-93-centos.repo

# FIX locales
RUN yum reinstall -y glibc-common

# Genera claves
RUN service sshd start

#--------------------------------------------------------------------------------
# Aca terminaron los procesos pesados. Si se cambian cosas de aca hacia abajo
#  el build igual será rapido
#--------------------------------------------------------------------------------

# Seteamos timezone
RUN cp -fv /usr/share/zoneinfo/America/Argentina/Cordoba /etc/localtime

# Ajustes para usar /sbin/init
RUN rm /etc/init/start-ttys.conf /etc/init/tty.conf
RUN chkconfig exim off
RUN chkconfig iptables off
RUN chkconfig crond off

# Setup sudo
RUN echo "ftsender ALL=(ALL)       NOPASSWD: ALL" > /etc/sudoers.d/ftsender

# Setup users
RUN adduser ftsender && su -c 'mkdir /home/ftsender/.ssh' ftsender && su -c 'chmod 0700 /home/ftsender/.ssh' ftsender

# Upload authorized_keys
COPY authorized_keys /home/ftsender/.ssh/authorized_keys
RUN chmod 0600 /home/ftsender/.ssh/authorized_keys && chown ftsender.ftsender -R /home/ftsender/.ssh

# RUN passwd --delete root
# RUN passwd --delete ftsender

# Setup ssh
# RUN cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
# RUN echo -e "Protocol 2\nPermitRootLogin yes\nPermitEmptyPasswords yes\nGSSAPIAuthentication no\nUsePAM no" > /etc/ssh/sshd_config

# Setup supervisord
# RUN mkdir -p /etc/supervisor/conf.d /var/log/supervisor/
# COPY supervisor.conf /etc/supervisord.conf

EXPOSE 22

# CMD ["/usr/bin/supervisord"]
CMD ["/sbin/init"]

