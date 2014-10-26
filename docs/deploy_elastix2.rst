.. highlight:: bash


###################
Deploy en Elastix 2
###################

Este documento describe el proceso de deploy de FTS en Elastix 2.

.. code::

    $ asterisk -V
    Asterisk 11.13.0

    $ uname -a
    2.6.18-398.el5

    $ cat /etc/redhat-release
    CentOS release 5.11 (Final)


***********************
Preparación para deploy
***********************

.. code::

    $ sudo yum install python-simplejson


**********************
Parámetros de Asterisk
**********************

Antes de realizar el deploy, hace falta setear en el archivo
de inventario las siguientes variables:


.. code::

    fts_distribution=elastix2

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

    $ vim /etc/nginx/nginx.conf


para que quede, por ejemplo:

.. code::

    server {
        listen       81;
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

Descomentar ``enabled`` y utilizar puerto ``7088``:

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


**************************
Sox y conversion de audios
**************************

La version de ``sox`` en CentOS 5 requiere parametros diferentes para realizar correctamente
la conversión de los archivos de audio.

Por lo tanto, hace falta que en el archivo de invetario, la variable ``dj_sett_TMPL_FTS_AUDIO_CONVERSOR`` este
seteada correctamente. En el archivo de inventario de referencia (al final de esta página) se encuentra
la configuración de ``dj_sett_TMPL_FTS_AUDIO_CONVERSOR`` a utilizar.


*************************
Known Issues
*************************

1. El setup de Asterisk *NO* es realizado por los scripts de inicio.

2. La instalación de Nginx produce problemas porque intenta usar el puerto 80,
   que es usado por Apache.

3. En una primera prueba, la tabla de CDR no posee registros. Esto pudo suceder
   porque la BD de prueba no posee nros. de telefonos validos.

4. La llamada a plpython falla

.. code::

	[2014-10-25 16:59:31,909: ERROR/MainProcess] Task fts_daemon.tasks.depurar_campana[3f359a76-cf9e-41e6-8288-08c6e66bb11c] raised unexpected: InternalError('AttributeError: \'str\' object has no attribute \'format\'\nCONTEXT:  Traceback (most recent call last):\n  PL/Python function "recalculate_agregacion_edc_py_v1", line 227, in <module>\n    plpy.notice("recalculate_agregacion_edc_py_v1(): UPDATE AEDC - campana: {0} - nro_intento: {1}".format(\nPL/Python function "recalculate_agregacion_edc_py_v1"\n',)
	Traceback (most recent call last):
	  File "/home/ftsender/deploy/virtualenv/lib/python2.6/site-packages/celery/app/trace.py", line 240, in trace_task
	    R = retval = fun(*args, **kwargs)
	  File "/home/ftsender/deploy/virtualenv/lib/python2.6/site-packages/celery/app/trace.py", line 437, in __protected_call__
	    return self.run(*args, **kwargs)
	  File "/home/ftsender/deploy/app/fts_daemon/tasks.py", line 35, in depurar_campana
	    DepuradorDeCampanaWorkflow().depurar(campana_id)
	  File "/home/ftsender/deploy/app/fts_daemon/services/depurador_de_campana.py", line 87, in depurar
	    self._depurar(campana)
	  File "/home/ftsender/deploy/app/fts_daemon/services/depurador_de_campana.py", line 45, in _depurar
	    campana.recalcular_aedc_completamente()
	  File "/home/ftsender/deploy/app/fts_web/models.py", line 1517, in recalcular_aedc_completamente
	    _plpython_recalcular_aedc_completamente(self)
	  File "/home/ftsender/deploy/app/fts_web/models.py", line 1817, in _plpython_recalcular_aedc_completamente
	    [campana.id, campana.cantidad_intentos])
	  File "/home/ftsender/deploy/virtualenv/lib/python2.6/site-packages/django/db/backends/util.py", line 53, in execute
	    return self.cursor.execute(sql, params)
	  File "/home/ftsender/deploy/virtualenv/lib/python2.6/site-packages/django/db/utils.py", line 99, in __exit__
	    six.reraise(dj_exc_type, dj_exc_value, traceback)
	  File "/home/ftsender/deploy/virtualenv/lib/python2.6/site-packages/django/db/backends/util.py", line 53, in execute
	    return self.cursor.execute(sql, params)
	InternalError: AttributeError: 'str' object has no attribute 'format'
	CONTEXT:  Traceback (most recent call last):
	  PL/Python function "recalculate_agregacion_edc_py_v1", line 227, in <module>
	    plpy.notice("recalculate_agregacion_edc_py_v1(): UPDATE AEDC - campana: {0} - nro_intento: {1}".format(
	PL/Python function "recalculate_agregacion_edc_py_v1"


***********************************
Archivo de inventario de referencia
***********************************

.. literalinclude:: ../deploy/hosts-virtual-pruebas-elastix2

