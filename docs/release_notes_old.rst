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
