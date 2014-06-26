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

* FTS-197 - La exportación de reportes en CSV realiza un SELECT de los datos.
  En estos casos Django/Python **almacena el resultado en memoria**. Esto deberia
  implementarse utilizando un server-side cursor.
* FTS-231 - El daemon **no finaliza** las campañas inmediantamente cuando
  la fecha de fin es futura pero ya no hay actuaciones que apliquen
* FTS-235 - El proceso de **reciclado de BD de contactos** realiza SELECT e inserta
  de a 1 contacto por vez, lo que lo hace poco eficiente
* FTS-137 FTS-199 - Al bajar el proceso de daemon, se finalizan todos los servicios.
  Si hay llamadas en curso **se pierden eventos** porque el servidor FastAgi
  se baja inmediantamente.
* FTS-136 - No se chequea el **resultado de llamada AGI**, lo que puede generar perdida
  de eventos si el llamado AGI() falla.
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

