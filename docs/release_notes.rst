Release Notes
=============

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

* Deploy de workers Celery

Bugs solucionados
.................

* FTS-169 - Reporta problemas con reload de configuracion de Asterisk
* FTS-206 - Valida y acepta csv con una sola columna (sin delimitador)

Otras mejoras
.............

* Unificación de archivos de dependencias y librerías Python

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
* FTS-248 - Luego de finalizar manualmente una campaña, el sistema permite ser
  modificandola (ej: des-pausarla), lo que podría causar problemas en el sistema.
  Actualmente, el usuario debe recordar NO des-pausar las campañas finalizadas
  manualmente.
