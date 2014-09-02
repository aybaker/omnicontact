Release Notes previas
=====================

Sprint 5 - 25 de junio de 2014
------------------------------

Nueva funcionalidad
...................

* Reciclado de campaña y base de datos de contactos
* Supervisión: mostrar estado actual del Daemon
* Derivación de llamadas
* Refrescar automaitcamente pantalla de supervisión
* Listado de contactos q' presionaron una opción (en vivo, estilo supervisión)


Deploy
......

* Deploy automatico de configuracion de PostgreSql
* Deploy de procedimientos almacenados plpythonu
* Armado de ambientes de testing y de deploy

Bugs solucionados
.................

* Alta de campaña: error 500 si conversion de audio falla


Sprint 6 - 11 de julio de 2014
------------------------------

Nueva funcionalidad
...................

* Implementacion de Celery para ejecución de tareas asincronas / en background
* Finalización manual de campañas en background
* FTS-212 - Nuevas formas de reciclado de campaña (Ocupados/No contestó/Número erróneo/Llamada errónea)
* FTS-234 - Validación consistencia de fechas y actuaciones de campañas
* FTS-231 - Daemon evita finalizar campañas que posean llamadas en curso
* FTS-152 - Depuración de eventos de contactos
* FTS-205 - Depuración de BD de contactos
* FTS-208 - Mejora UI de carga de audio de campaña


Deploy
......

* Deploy de Redis
* Deploy de workers Celery


Bugs solucionados
.................

* FTS-169 - Reporta problemas con reload de configuracion de Asterisk
* FTS-206 - Valida y acepta csv con una sola columna (sin delimitador)


Otras mejoras
.............

* Unificación de archivos de dependencias y librerías Python
* Ajustes a instrucciones de deploy


Sprint 7 - 25 de julio de 2014
------------------------------

Instrucciones de deploy
.......................

.. code::

    $ ssh deployer@192.168.99.224
    $ ./deploy.sh sprint7-fixes <INVENTARIO>

Nueva funcionalidad
...................

* FTS-13 - Eliminar Grupos de Atención
* FTS-14 - Modificar Grupos de Atención
* FTS-173 - Procesos largos deben mostrar progreso o mensaje
* FTS-211 - Agregar 'date picker' para fechas + widget para horarios
* FTS-240 - Permitir acceso a todos los tabs al crear y reciclar campaña
* FTS-246 - Reciclado de campañas, filtrando por más de un estado
* FTS-248 - Implementación de estado DEPURADA para Campaña, evita
  problemas de acceso concurrente e inconsistencias desde que la campaña
  es finalizada hasta que es depurada.
* FTS-252 - Mostrar en web la versión de la aplicación
* FTS-254 - Usar colores de FreeTech en UI
* FTS-259 - Borrar campaña
* FTS-260 - Identificar usuarios del sistema

Deploy
......

* Generacion de ambiente de desarrollo usando Docker

Bugs solucionados
.................

* FTS-249 - FIX: paths concatenados, en vez de generados con os.path.join()
* FTS-250 - FIX: FTS_BASE_DATO_CONTACTO_DUMP_PATH requiere finalizar con /
* FTS-255 - FIX "error interno" al intentar depurar BD de Contactos
* FTS-261 - FIX: script de inicio no hace reload desde scripts de deploy
* FTS-262 - FIX: script de deploy no deploya version más reciente



Sprint 8 - 4 de agosto de 2014
------------------------------

Instrucciones de deploy
.......................

.. code::

    $ ssh deployer@192.168.99.224
    $ ./deploy.sh sprint8-fixes <INVENTARIO>

Nueva funcionalidad
...................

* FTS-268 (y otras) - Derivación externa de llamadas
* FTS-279 - Crea comando para crear usuario para sistema web

Deploy
......

* FTS-274 - Hacer configurables limites de originates y otras settings del sistema
* FTS-267 - Implementa Supervisor para workers Celery
* FTS-199 - Separar distintos daemons

Bugs solucionados
.................

* FTS-207 - Reporte: unificar opciones invalidas en pie chart
* FTS-42 - Separar frameworks (bootstrap) de las customizaciones


Sprint 9 - 20 de agosto de 2014
-------------------------------


Instrucciones de deploy
.......................


.. code::

    $ ssh deployer@192.168.99.224
    $ ./deploy.sh sprint9-fixes <INVENTARIO>


Nueva funcionalidad: Templates de Campañas
..........................................

* FTS-285 FTS-286 - Creacion de templates de campañas
* FTS-287 FTS-289 - Creación de campañas desde templates de campaña
* FTS-288 - Listado y borrado de templates de campañas
* FTS-290 - Daemon: ignorar templates al buscar campañas a ejecutar

Nueva funcionalidad: Audios predefinidos
........................................

* FTS-291 FTS-292 - Creación de audios predefinidos
* FTS-292 - ABM y listado de audios predefinidos
* FTS-293 - Update de campañas y templates de campañas: permite seleccion
  de audios predefinidos
* FTS-294 - Conversión de formato de archivos de audios para audios predefinidos
