Release Notes
=============

Sprint 13 - 29 de septiembre de 2014 - 14 de octubre de 2014
---------------------------------------------------------------

Ver Sprint 14 (las notas de release estan unificadas)

Sprint 14 - 15 de octubre de 2014 - 28 de octubre de 2014
---------------------------------------------------------------


Cambios en archivo de inventario
................................

Para soportar CentOS, Elastix 2 y Elastix 3 fue necesario agregar una variable
al archivo de inventario.

A los archivos de inventarios existentes, usados para deployar en CentOS 6, hay
que agregarle:

.. code::

    fts_distribution: centos6


Para hacer deploy en Elastix 2:

.. code::

    fts_distribution: elastix2


Para hacer deploy en Elastix 3:

.. code::

    fts_distribution: elastix3

También se crearon 2 documentos: *Deploy en Elastix 2* y *Deploy en Elastix 3* con
instrucciones detalladas.



Instrucciones de deploy
.......................

En este sprint se produjeron varios cambios incompatibles en la BD. Luego de
realizar el deploy, los datos existentes de BD y campañas no será utilizables. 

Para realizar el deploy:

.. code::

    $ ssh deployer@192.168.99.224
    $ ./deploy.sh sprint14-fixes <INVENTARIO>

Para crear usuarios, es necesario loguearse en el servidor con el usuario `ftsender`
y ejecutar `/home/ftsender/deploy/bin/manage.sh create_ftsender_user`:

.. code::

    $ host> ssh ftsender@server-or-ip
    $ server> /home/ftsender/deploy/bin/manage.sh create_ftsender_user


Migraciones de datos
....................

.. code::

	00eb06a Agrega migración para el cambio de nombre del atributo estadistica.
	d31dc82 Agrega migración para el nuevo atributo Campana.Campana.metadata_estadisticas.
	114c074 Aplica migracion solo cuando la BD es PostgreSql
	cdcdbc7 Agrega migración para el atributo DuracionDeLlamada.eventos_del_contacto.
	ec49420 Agrega migración que crea la tabla CDR.
	c4bff60 Agrega migración para la modificación de modelos DuracionDeLlamada.
	348a131 Agrega migración para el modelo DuracionDeLlamada.
	f22fc47 Agrega migración para el nuevo atributo duracion_de_audio.


Issues resueltos
..............................................

* FTS-328 - Generar datos en tabla CDR para desarrollar y probar la funcionalidad
* FTS-333 - Investigar datos de tabla CDR: cómo hacer JOIN con tablas de FTS
* FTS-336 - Leer CSV usando utf-8
* FTS-334 - Estadísticas de contactos que escucharon todo el mensaje
* FTS-335 - Campaña: agregar campo "duracion de audio", o "duracion media de audio", etc. (para usar de referencia en reportes)
* FTS-337 - Búsque de llamadas por número de telefono
* FTS-344 - Realizar test manual completo al sistema

Soporte para Elastix
..............................................

* FTS-329 - Soportar deploy en Elastix 2 y Elastix 3
* FTS-339 - Soportar ejecución en Elastix 2 y Elastix 3


Known BUGs
----------

* FTS-315 - ParserCsv abre file pero NO lo cierra

Known issues
------------

* FTS-327 - Campos extras en TTS: deberian incluir tipo de dato ademas del nombre del campo
* FTS-197 - La exportación de reportes en CSV realiza un SELECT de los datos.
  En estos casos Django/Python **almacena el resultado en memoria**. Esto deberia
  implementarse utilizando un server-side cursor.
* FTS-231 - El daemon **no finaliza** las campañas inmediantamente cuando
  la fecha de fin es futura pero ya no hay actuaciones que apliquen
* FTS-235 - El proceso de **reciclado de BD de contactos** realiza SELECT e inserta
  de a 1 contacto por vez, lo que lo hace poco eficiente
* FTS-137 FTS-199 - Al bajar el proceso de daemon, se finalizan todos los servicios.
  Si hay llamadas en curso **se pierden eventos** porque el servidor FastAgi
  se baja inmediantamente. Tambien puede suceder algo parecido en workers Celery.
* FTS-136 - No se chequea el **resultado de llamada AGI**, lo que puede generar perdida
  de eventos si el llamado AGI() falla.
* FTS-174 - Sobrepaso de limites si AMI/HTTP falla: sólo sucende en un caso muy particular,
  si existen llamadas en curso cuando el daemon arranca (porque se reinició, por ejemplo),
  y el primer request que se hace via AMI / HTTP fallara, puede suceder que se realicen
  ORIGINATES produciendo un sobrepaso en el límite de canales.
* FTS-189 - El sistema de deploy no configura **logrotate**, lo que puede
  hacer que el sistema genere grandes archivos de logs
* FTS-176 - No se ha verificado el comportamiento del sistema ante cambios
  de **zona horaria** o la aparición de **leap seconds**.
* FTS-125 FTS-173 - Actualmente todos los procesos son **sincronos**, realizados en el contexto
  del request al servidor web. Hay procesos que sería conveniente hacerlos de
  manera asíncrona (ej: la creación de la BD de contactos)
* FTS-144 - El componente que se comunica via HTTP a la interfaz AMI de Asterisk
  **no mantiene una sesion**, por lo tanto, debe loguearse cada vez que consulta
  el estado de las llamadas. Esto hace que se generen muchos logs, y no es la
  forma más eficiente de comunicarse con Asterisk.
* FTS-244 - El paso del tiempo (para implementar pausas, o medir el paso del tiempo)
  es realizado de una forma quizá demansiado simplistica, y puede tener consecuencias
  en casos puntuales como ante **cambios de zona horaria**, o ante el ajuste de la hora
  por parte del daemon **ntp**.
* FTS-245 - Campañas y bases de datos que quedan "en definicion" nunca son borradas
* FTS-264 - Usuario de BD requiere rol de superusuario
* FTS-265 - Realizar configuracion fina de Celery
* FTS-266 - Celery: evitar re-programar tareas en curso o encoladas
