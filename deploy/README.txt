
Aqui estan los archivos relacionados con deploys, ya sean en servidores
reales, docker, etc.

============
Docker / Fig
============

Instalación
-----------

Antes que nada, hace falta instalar Docker:

    http://docs.docker.com/installation/ubuntulinux/#ubuntu-trusty-1404-lts-64-bit

Y para que no haga falta usar 'sudo':

    $ sudo adduser $USER docker

Ahora hará falta reiniciar el equipo para que tome los cambios producidos
por el comando anterior


Build de contenedor Docker
--------------------------

Para utilizar Docker/Fig, es necesario crear un virtualenv en el
directorio 'deploy/docker-dev/'.

Para crearlo, ejecutar:

    $ virtualenv deploy/virtualenv-fig
    $ ./deploy/virtualenv-fig/bin/pip install -r deploy/requirements.txt

Para crear las imagenes de Docker (esto hay que realizarlo solo una vez):

    $ cp deploy/docker-dev/asterisk/conf-build/yum.conf.extra.sample deploy/docker-dev/asterisk/conf-build/yum.conf.extra
    $ vi deploy/docker-dev/asterisk/conf-build/yum.conf.extra
    $ ./deploy/docker-dev/build.sh


========
Asterisk
========

Para iniciar Asterisk:

    $ ./deploy/docker-dev/run.sh


Asterisk + CDR + PostgreSql 
===========================

Para que Asterisk pueda insertar registros CDR, es necesario
configurar PostgreSql para que pueda ser accedido desde Docker.

Para esto hay que editar 'postgresql.conf':

    $ sudo vim /etc/postgresql/9.3/main/postgresql.conf

Y agregar '172.17.42.1' a listen_addresses. Por ejemplo, si el valor
inicial es:

    listen_addresses = '127.0.0.1'

hay que modificarlo para que diga:

    listen_addresses = '127.0.0.1,172.17.42.1'

Luego de guardar el archivo, reiniciar el servicio de PostgreSql:

    $ sudo service postgresql restart

Chequeo de logs
---------------

Para chequear los logs de PostgreSql:

    $ sudo tail -f /var/log/postgresql/postgresql-9.3-main.log

Si se encuentran mensajes del estilo:

    FATAL:  no pg_hba.conf entry for host "172.17.0.XXX", user "XXX", database "XXX", SSL off

es porque PostgreSql no permite acceso a la BD desde los IP de Docker. Esto mismo
error se refleja en los logs de Asterisk con mensajes del estilo:

    asterisk_1 | [Oct 13 15:34:51] ERROR[64][C-00000000]: cdr_pgsql.c:191 pgsql_log: Unable to connect to database server 172.17.42.1.  Calls will not be logged!
    asterisk_1 | [Oct 13 15:34:51] ERROR[64][C-00000000]: cdr_pgsql.c:192 pgsql_log: Reason: FATAL:  no pg_hba.conf entry for host "172.17.0.14", user "fts", database "fts", SSL on

Para solucionar esto, hace falta editar 'pg_hba.conf', y agregar
permisos a las conexiones provenientes desde '172.17.0.0/24':

    $ sudo vim /etc/postgresql/9.3/main/pg_hba.conf

Por ejemplo, si originalmente se usaba:

    host    all        all   127.0.0.1/32    md5

agregar una linea, para que quede:

    host    all        all   127.0.0.1/32    md5
    host    all        all   172.17.0.0/24   md5
