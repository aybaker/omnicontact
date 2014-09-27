#
# TODO:
#  * hacer accesibles archivos de audio
#
# Usuarios SIP:
#  - USER: test_user1 - PASS: 1234
#  - USER: test_user2 - PASS: 1234
#
# Las llamadas realizadas al numero '319751355727335' seran
#  routeadas al usuario sip 'test_user1'
#
# ----- Puertos usados por Asterisk -----
#
# tcp        0      0 0.0.0.0:5038                0.0.0.0:*                   LISTEN      -                   
# tcp        0      0 0.0.0.0:2000                0.0.0.0:*                   LISTEN      -                   
# tcp        0      0 0.0.0.0:7088                0.0.0.0:*                   LISTEN      -                   
# udp        0      0 0.0.0.0:2727                0.0.0.0:*                               -                   
# udp        0      0 0.0.0.0:4520                0.0.0.0:*                               -                   
# udp        0      0 0.0.0.0:4569                0.0.0.0:*                               -                   
# udp        0      0 0.0.0.0:5000                0.0.0.0:*                               -                   
# udp        0      0 0.0.0.0:5060                0.0.0.0:*                               -                   
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

EXPOSE 2000 2727 4520 4569 5000 5038 5060 7088

COPY in_docker_start.sh /in_docker_start.sh

COPY conf /opt/asterisk-11/etc/asterisk/

CMD ["/in_docker_start.sh"]

