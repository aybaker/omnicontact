.. highlight:: bash


###################
Deploy en Elastix 3
###################

Este documento describe el proceso de deploy de FTS en Elastix 3. Estas
instrucciones y comandos fueron probados en Elastix 3.0.0 RC1, 
instalado usando la imagen ISO ``Elastix-3.0.0-RC1-i386-bin-17jun2014.iso``.

.. code::

    $ asterisk -V
    Asterisk 11.8.1


**********************
Parámetros de Asterisk
**********************

Antes de realizar el deploy, hace falta setear en el archivo
de inventario las siguientes variables:


.. code::

    fts_distribution=elastix3

    dj_sett_ASTERISK_USERNAME=admin
    dj_sett_ASTERISK_PASSWORD=**********


El valor de ``dj_sett_ASTERISK_PASSWORD`` debe ser obtenido de
``/etc/asterisk/manager.conf``.


**********************
Nginx
**********************

Luego de que se instale Nginx, el deploy fallará, porque hace falta
modificar manualmente el puerto 80 por alguno que no esté en uso (ej: 81)


.. code::

    $ vim /etc/nginx/conf.d/default.conf


para que quede, por ejemplo:

.. code::
    
	server {
    	listen       81 default_server;
    	server_name  _;

Esto hace falta porque porque el puerto 80 es utilizado por Apache.

Una vez que se haya editado dicho archivo, se debe reiniciar el script
de deploy, y esta segunda vez (y los futuros deploys) se realizará correctamente.


*************************
Configuración de Asterisk
*************************

Para el correcto funcionamiento del sistema, hace falta realizar las
siguientes modificaciones:


1. Habilitar AMI via HTTP
=========================

.. code::

    $ vim /etc/asterisk/http.conf

Comentar ``prefix`` y utilizar puerto ``7088``:

.. code::

    enabled=yes
    bindport=7088
    ;prefix=asterisk

.. code::

    vim /etc/asterisk/manager.conf

Agregar ``webenabled``:

.. code::

    [general]
    enabled = yes
    webenabled = yes
    port = 5038
    bindaddr = 0.0.0.0


2. Incluir dialplan generado por FTS
====================================

Por ejemplo, editar ``/etc/asterisk/extensions_custom.conf``:

.. code::

    $ vim /etc/asterisk/extensions_custom.conf


Y agregar el ``#include``:
    
.. code::

    #include /etc/ftsender/asterisk/extensions.conf
    
El path especificado debe ser el mismo path configurado en la variable
``dj_sett_FTS_DIALPLAN_FILENAME`` en el archivo de inventario. 


3. Incluir queues generado por FTS
==================================

Por ejemplo, editar ``/etc/asterisk/queues_custom.conf``:

.. code::

    $ vim /etc/asterisk/queues_custom.conf


Y agregar el ``#include``:
    
.. code::

    #include /etc/asterisk/queues_custom.conf
    
El path especificado debe ser el mismo path configurado en la variable
``dj_sett_FTS_QUEUE_FILENAME`` en el archivo de inventario. 


4. Configurar CDR
=================


.. note::

    Estos pasos para configurar el CDR son un bosquejo, todavia
    no han sido probados.


Antes que nada hace falta activar el modulo cdr_pgsql:

.. code::

    $ vim /etc/asterisk/modules.conf


y comentar la línea que dice ``noload => cdr_pgsql.so``, de manera que quede:

.. code::

    ;noload => cdr_pgsql.so


Crear el archivo ``cdr_pgsql.conf``:

.. code::

    $ vim /etc/asterisk/cdr_pgsql.conf

de manera que contenga los parametros de conexion:

.. code::

    [global]
    hostname=127.0.0.1
    port=5432
    dbname=ftsender
    user=ftsender
    password=<PASSWORD>
    table=cdr
    encoding=UTF8
    timezone=UTC


El ``password`` para conectarse a la BD es el especificado
en la configuración ``db_password`` del archivo de inventario.


*************************
Known Issues
*************************

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


***********************************
Archivo de inventario de referencia
***********************************
    
El archivo de inventario utilizado para hacer el deploy fue
el siguiente:

.. literalinclude:: ../deploy/hosts-virtual-pruebas-elastix3
