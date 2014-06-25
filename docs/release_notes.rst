Release Notes
=============

Sprint 5 - 25 de junio de 2014
------------------------------

Nueva funcionalidad
......

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


Known issues
------------

* FTS-197 La exportación de reportes en CSV realiza un SELECT de los datos.
  En estos casos Django/Python almacena el resultado en memoria. Esto deberia
  implementarse utilizando un server-side cursor.
* FTS-231 El daemon no finaliza las campañas inmediantamente cuando
  la fecha de fin es futura pero ya no hay actuaciones que apliquen
* FTS-235 El proceso de reciclado de contactos realiza SELECT e inserta
  de a 1 contacto por vez, lo que lo hace poco eficiente
* FTS-137 Al bajar el proceso de daemon, se finalizan todos los servicios.
  Si hay llamadas en curso se pierden eventos porque el servidor FastAgi
  se baja inmediantamente.
* FTS-189 El sistema de deploy no configura logrotate, lo que puede
  hacer que el sistema genere grandes archivos de logs

