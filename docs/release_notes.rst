Release Notes
=============

Sprint 12 - 16 de septiembre de 2014 - 29 de septiembre de 2014
---------------------------------------------------------------


Instrucciones de deploy
.......................

ATENCION: en el presente Sprint se implementaron cambios en la BD. Antes de realizar el deploy del sistema,
confirme que no haya campañas pausadas o en ejecución. El proceso de migración de la BD dejará las campañas y
templates en un estado inconsistente y no deberian ser utilizadas ni recicladas.

.. code::

    $ ssh deployer@192.168.99.224
    $ ./deploy.sh sprint12-fixes <INVENTARIO>

Para crear usuarios, es necesario loguearse en el servidor con el usuario `ftsender`
y ejecutar `/home/ftsender/deploy/bin/manage.sh create_ftsender_user`:

.. code::

    $ host> ssh ftsender@server-or-ip
    $ server> /home/ftsender/deploy/bin/manage.sh create_ftsender_user


Migraciones de datos
....................

.. code::

	* commit 2bd71d0b3bc2bfe20cf5412286f1e6250994a067
	  A     fts_web/migrations/0025_auto__add_audiodecampana.py

	* commit c930e22320a35f0cd6ee62b35bf9400d1091b531
	  A     fts_web/migrations/0026_auto__del_field_campana_audio_asterisk__del_field_campana_audio_origin.py

	* commit cdbcc8dcc90e30b322e1968279eef639e1e37bfe
	  A     fts_web/migrations/0027_auto__chg_field_audiodecampana_tts.py

	* commit edfdfa32cc2532cb44b678ad82e305a102faf03d
	  A     fts_web/migrations/0028_auto__add_unique_audiodecampana_orden_campana.py

	* commit 1bda83dd61b86dc71bec31c372247626c4b87c71
	  A     fts_web/migrations/0029_auto__add_field_audiodecampana_audio_descripcion.py


TTS / Multiples TTS
..............................................

* FTS-310 - UI: Alta de campaña (funcionalidad avanzada)
* FTS-311 - UI: Alta de campaña: volver a permitir modificación de BD
* FTS-306 - Campos fecha/hora: Daemon: obtener metadatos de BD
* FTS-307 - Campos fecha/hora: Generador de dialplan
* FTS-325 - Template de Campaña: agregar BDC de referencia
* FTS-326 - Multiples TTS: mejoras en generador de Dialplan

Diferidos para próximo Sprint
.............................

* FTS-297 - Soporte para multiples sistemas de TTS (requiere FTS-326)


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
