Release Notes
=============

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

* FTS-255 - FIX "error interno" al intentar depurar BD de Contactos
* FTS-261 - FIX: script de inicio no hace reload desde scripts de deploy
* FTS-262 - FIX: script de deploy no deploya version más reciente


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
