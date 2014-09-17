#
# Para crear imagen:
#
#    $ docker build -t hgdeoro/fts-asterisk-dev .
#
# Para lanzar container:
#
#    $ docker run -ti hgdeoro/fts-asterisk-dev
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
RUN rpm -Uvh https://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm

# Instalas paquetes. 1ra linea: basicos. Demas lineas: instalados por Ansible
#  1) '--enablerepo centosplus' workaround p/poder instalar libselinux-python
#       Ver: https://bugs.centos.org/view.php?id=7126

RUN yum groupinstall -y "Development tools"

RUN yum --enablerepo centosplus install -y \
    openssh-server sudo passwd 

RUN yum --enablerepo centosplus install -y \
    wget 

WORKDIR /

RUN wget http://downloads.asterisk.org/pub/telephony/asterisk/releases/asterisk-11.9.0.tar.gz

RUN tar xzf asterisk-11.9.0.tar.gz

WORKDIR /asterisk-11.9.0

RUN yum --enablerepo centosplus install -y \
    ncurses-devel

RUN yum --enablerepo centosplus install -y \
    libxslt-devel

RUN yum --enablerepo centosplus install -y \
    sqlite-devel

RUN ./configure --prefix=/opt/asterisk-11

RUN make -j 2
RUN make install
RUN make samples

# EXPOSE 22
# EXPOSE 8088

COPY start.sh /start.sh

CMD ["/start.sh"]
