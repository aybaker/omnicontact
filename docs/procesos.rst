Procesos
========


.. image:: arquitectura.png


Estos son los procesos que corren en servidores productivos.

Los paths indicados aquí son relativos al directorio base de
los fuentes del proyectos, o sea, *no* se refieren a los paths
en donde se encontrarán en el servidor.

Aplicación Web: Django + uWSGI
---------------------------------------------------------------

Este proceso es gestionado directamente con "init scripts":

.. code::

    deploy/roles/ftsender_server/templates/etc/init.d/ftsender-daemon

los settings son tomados desde:

.. code::

    deploy/roles/ftsender_server/templates/ftsender_uwsgi.ini

El reload y stop del servicio es realizado a travez del FIFO.

.. note::

    Si este servicio no corre, la aplicación web queda inaccesible, pero
    **el resto del sistema funciona correctamente**, y no implica ninguna
    pérdida de datos.


SupervisorD
---------------------------------------------------------------

SupervisorD es utilizado para lanzar y gestionar los demas daemons.

El archivo de configuración utilizado es:

.. code::

    deploy/roles/ftsender_server/templates/etc/supervisord.conf

Cada uno de los servicios que son lanzados poseen una sección
en el archivo de configuración, de la forma: ``[program:NOMBRE-DEL-DAEMON]``.

.. code::

    [program:fts-llamador-poll-daemon]
    [program:fts-fastagi-daemon]
    [program:fts-chequeador-campanas-vencidas]
    [program:fts-celery-worker-esperar-finaliza-campana]
    [program:fts-celery-worker-finalizar-campana]


Daemon llamador
---------------

fts-llamador-poll-daemon
++++++++++++++++++++++++

Este servicio se encarga de interactuar con Asterisk para generar
las llamadas.

El daemon está implementado en:

.. code::

    fts_daemon/poll_daemon/main.py


.. note::

    Si este servicio no corre, el sistema **no generará más llamadas**.
    No es un problema menor, pero tampoco es tan grave, teniendo en
    cuenta que **no hay pérdida de datos**.

Daemon FastAGI
--------------

fts-fastagi-daemon
++++++++++++++++++

Este servicio recibe las llamadas FastAGI generadas por Asterisk.

Asterisk genera llamadas FastAGI para informar los eventos, detectados/reportados
en distintas partes del dialplan. Algunos de los **eventos** existentes son:

 * aceptación de llamada (cuando la persona atiende)
 * no-realización de llamada (ocupado, problema con canal, etc.)
 * ingreso de dígitos por parte de la persona

Este servicio puede verse como un "proxy". Sólo recibe eventos AGI y por
cada evento, se realiza un INSERT en la tabla de eventos.

El daemon está implementado en:

.. code::

    fts_daemon/fastagi_daemon.py

.. danger::

    Este servicio es el más crítico del sistema, debido a que es el encargado
    de recibir los *eventos* detectados por Asterisk.

    Si el servicio no corre mientras haya campañas en curso, los eventos
    producidos **se pierden**. No sabremos quién atendió y quién no,


Chequeador de campañas vencidas
-------------------------------

fts-chequeador-campanas-vencidas
++++++++++++++++++++++++++++++++

Este daemon realiza una tarea periódica, que consta de 2 partes:

1. busca campañas vencidas y las marca como finalizadas
2. busca campañas finalizadas, y las encola para realizar los procesos de cierre y depuración

El daemon está implementado en:

.. code::

    fts_daemon/services/finalizador_vencidas_daemon.py

.. note::

    Si este servicio no corre, el sistema **no procesará las campañas finalizadas**.
    No es un problema grave si tenemos en cuenta que no se producen perdidas de datos,
    pero produce problemas a los usuarios, ya que ellos no podrán ver los reportes
    ni reutilizar dicha campaña.


Worker Celery esperador
-----------------------

fts-celery-worker-esperar-finaliza-campana
++++++++++++++++++++++++++++++++++++++++++

Este worker de Celery lo unico que hace es chequear las llamadas en curso,
esperando a que la campaña en cuestión no posea llamadas en curso en Asterisk.

Una vez que se detecte que no hay llamadas en curso, encola un trabajo para que
``fts-celery-worker-finalizar-campana`` realice los procesos de finalizacion y depuración.

Las tasks asíncronas, que se ejecutarán en workers de Celery, están definidas en:

.. code::

    fts_daemon/tasks.py

.. note::

    Si este servicio no corre, el sistema **no procesará las campañas finalizadas**.
    No es un problema grave si tenemos en cuenta que no se producen perdidas de datos,
    pero produce problemas a los usuarios, ya que ellos no podrán ver los reportes
    ni reutilizar dicha campaña.


Worker Celery finalizador
-------------------------

fts-celery-worker-finalizar-campana
+++++++++++++++++++++++++++++++++++

Este worker de Celery realiza todas las tareas de finalización y depuración de
la campaña, incluyendo generación de reporte, limpieza de tablas, etc.

Las tasks asíncronas, que se ejecutarán en workers de Celery, están definidas en:

.. code::

    fts_daemon/tasks.py

.. note::

    Si este servicio no corre, el sistema **no procesará las campañas finalizadas**.
    No es un problema grave si tenemos en cuenta que no se producen perdidas de datos,
    pero produce problemas a los usuarios, ya que ellos no podrán ver los reportes
    ni reutilizar dicha campaña.
