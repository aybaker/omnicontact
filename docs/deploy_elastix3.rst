.. highlight:: bash


Deploy en Elastix 3
===================

Este documento describe el proceso de deploy de FTS en Elastix 3. Estas
instrucciones y comandos fueron probados en Elastix 3.0.0 RC1, 
instalado usando la imagen ISO ``Elastix-3.0.0-RC1-i386-bin-17jun2014.iso``.


Deploy
------

El script de deploy debe incluir el parametro ``--skip-tags=asterisk``:

.. code::

    $ ./deploy.sh sprint12-fixes --skip-tags=asterisk <INVENTARIO>


Si se utilizara directamente el script de build:

.. code::

    $ ./build.sh -i INVENTARIO --skip-tags=asterisk


Esto es necesario porque Elastix ya posee Asterisk instalado.


Nginx
-----

Luego de que se instale Nginx, hace falta modificar el puerto 80
por alguno que no esté en uso (ej: 81)


.. code::

    $ vim /etc/nginx/conf.d/default.conf


para que quede, por ejemplo:

.. code::
    
	server {
    	listen       81 default_server;
    	server_name  _;

Esto hace falta porque porque el puerto 80 es utilizado por Apache.


Known Issues
------------

1. El setup de Asterisk *NO* es realizado por los scripts de inicio.

2. La instalación de Nginx produce problemas porque intenta usar el puerto 80,
que es usado por Apache.

3. Luego de instalar el sistema, los servicios NO levantan por un largo tiempo,
incluyendo los servicios de FTSender (nginx, supervisord, fts) y hasta
el mismo Asterisk.

El problema es el proceso ``S66elastix-firstboot`` que se queda esperando
la respuesta del usuario:


.. code::

    root       894  0.1  0.0   5252  1572 ?        Ss   17:48   0:00 /bin/bash /etc/rc.d/rc 3
    root      2447  0.0  0.0   5120  1296 ?        S    17:48   0:00  \_ /bin/bash /etc/rc3.d/S66elastix-firstboot start
    root      2448  0.1  0.4  32964  8868 ?        S    17:48   0:00      \_ /usr/bin/php /usr/bin/elastix-admin-passwords --init
    root      2523  0.0  0.0   4860  1324 ?        S    17:48   0:00          \_ /usr/bin/dialog --no-cancel --output-fd 3 --backtitle Elastix password configuration (Screen 1 of 4) --insecure --passwordbox The Elastix system 


Haciendo kill de esos procesos se logra que el sistema termina de bootear. Y luego
puede lanzarse manualmente:


.. code::

    $ /etc/rc3.d/S66elastix-firstboot start
