Dialer Campaigns
================

Omnileads pone a disposición el concepto de campañas de discado automático a través de un discador predictivo.

** Importante: No se provee la funcionalidad de discador automático dentro de las prestaciones del software, para este tipo de campañas está contemplada la integración con `Wombat Dialer <https://www.wombatdialer.com/>`_ p. La utilización de ese software está supeditada a la adquisición de la correspondiente licencia con el fabricante de `Wombat Dialer <https://www.wombatdialer.com/purchase.jsp/>`_.
**


Para poner en funcionamiento este tipo de campañas, se debe contar con los siguientes requisitos:

Base de contactos: archivo con información de los números a contactar por parte de la campaña saliente.
Formulario de campaña (si estuviera previsto): es el formulario que se desplegará en la consola del agente cada vez que el discador contacte un número de la base.
Calificaciones: cada vez que el agente termine una llamada, se desplegará un listado de calificaciones para tipificar el resultado de la llamada gestionada.
Sitio Web Externo (en caso de trabajar con este tipo de interacción): es el Sitio web externo que se desplegará en la consola de comunicaciones del agente cada vez que el discador contacte un número de la base.

Para listar todas las campañas existentes se debe ingresar a Campañas > Campañas Dialer > Listado de campañas. En la pantalla se puede observar las campañas agrupadas por su estado.


Sobre cada campaña se pueden efectuar las siguientes acciones, ingresando al botón “Opciones” que está a la derecha de cada una:
Según su estado se puede pausar, activar o iniciar;
Se puede reciclar una campaña para reutilizar todas o algunas de sus configuraciones;
Ver las calificaciones y los reportes de dicha campaña;
Agregar agentes (sólo en las campañas activas, pausadas o inactivas)
Dar permisos para ver la campaña a los usuarios supervisores;
Editar o eliminar la campaña.

Ejemplo de acciones sobre una campaña pausada:


6.1.2. Creación de campaña

Ingresar a Campañas > Campañas Dialer > Nueva Campaña

El primer formulario que se despliega contiene los siguientes campos:

Nombre: es el nombre de referencia de la campaña.
Fecha Inicio: es la fecha en la que, estando activa la campaña y con agentes conectados, comenzará a discar.
Fecha Fin: es la fecha en la que, estando activa la campaña y con agentes conectados, dejará de discar, aunque haya aún números pendientes de marcar.
Calificación de campaña: es el grupo de calificaciones que se desplegará cada vez que el agente reciba una llamada de la campaña en su consola de comunicación.
Base de Datos de contactos: la base con números que la campaña va a marcar.
Formulario: en este campo, se indica si la nueva campaña va a trabajar con un formulario a la hora de desplegar la información del teléfono contactado por el discador, sobre la consola de agente. Además, se indica cúal es el formulario que se desplegará.
URL Externa: en este campo, se indica si la nueva campaña va a invocar un Sitio Web Externo por cada teléfono contactado por el discador, sobre la consola de agente. Además, se indica cúal es el “Sitio” que se desplegará.
Objetivo: es un valor numérico que representa la cantidad de gestiones que se propone realizar durante la campaña.



Una vez completados estos campos, se debe dar click al botón “Paso siguiente”.

La siguiente pantalla establece los parámetros de comportamiento de la campaña:

Cantidad Max. de llamadas: es la cantidad de canales telefónicos que serán utilizados para discar los números de la campaña, en simultáneo.
Tiempo de descanso entre llamadas: es el tiempo (en segundos) que cada agente tendrá de gracia, entre llamadas conectadas por el discador. Este parámetro toma sentido cuando el grupo de agentes al cual el agente que recibe la llamada pertenece, no tenga el tilde de “Auto-Pausa”, ya que en ese caso cuando se finaliza la llamada, el agente queda automáticamente en un estado de pausa.
Nivel de servicio: es un parámetro de tiempo (en segundos) para medir cuántas de las llamadas fueron contestadas dentro de esa franja de tiempo.
Estrategia de distribución: método de distribución de llamadas que usará la campaña sobre los agentes. Para campañas salientes, se recomienda RRmemory.
Importancia de la campaña: Es un parámetro lineal (del 1 al 10) que indica cuán importante son las llamadas de esta campaña respecto a otras, estableciendo prioridades para los agentes que trabajen en varias campañas en simultáneo. Si se deja el valor en “0” (por defecto) se mantiene equidad con el resto de las campañas.
Tiempo de espera en cola: es el tiempo (en segundos), que la llamada contactada quedará en cola de espera, aguardando que un agente se libere para conectarle la misma.
Grabar llamados: se debe tildar este check, en caso de requerir que los llamados sean grabados.
Detectar contestadores: se debe tildar este check, en caso de requerir que se detecten y eviten las llamadas con contestadores automáticos.
Audio para contestadores: se puede indicar la reproducción de un audio en caso que se detecte un contestador automático. Para que esté disponible el audio debe subirse previamente desde el menú Audios > Nuevo audio
Activar predictividad: Wombat Dialer ofrece una configuración que posibilita revisar estadísticas de efectividad de las llamadas. En función de esos resultados, en lugar de discar uno por uno los números de teléfono de la base de contactos, selecciona el promedio de llamadas que resultan exitosas y efectúa tantas llamadas en simultáneo en función de ese dato.
Factor de boost inicial: indica el valor por el cual se desea multiplicar el comportamiento de la predictividad. Por ejemplo: si el discador detectó que puede realizar tres llamadas en simultáneo porque es el resultado que le arroja la estadística de comunicaciones exitosas, colocando “2” en el factor de boost inicial se le pide al discador que duplique ese valor y realizará entonces seis llamadas a la vez.


Luego de completar todos los campos, se debe presionar el botón “Paso siguiente”.

En la siguiente pantalla se configuran las opciones de calificación, seleccionando del desplegable una a una las calificaciones que se utilizarán para las llamadas dentro de la campaña. Además, se deberá indicar si se trata de una calificación de Gestión (que desencadenará alguna otra acción, como por ejemplo un nuevo formulario) o bien de una calificación “Sin Acción”.



Se guardan los cambios haciendo click en “Paso siguiente”. Se despliega entonces la opción de agregar parámetros extra al webform. Este paso nos brinda la posibilidad de agregar los parámetros que necesitamos exportar en caso de utilizar un sitio externo. Está previsto que funcione con el binomio tag/columna, por eso para cada campo se presentan dos cajas de texto vacías. Esto permitirá vincular los datos de las columnas de las bases de datos que debemos trasladar desde OML al sitio externo que estemos utilizando.



Nuevamente se presiona el botón “Paso siguiente” y llegamos a la configuración que determina cuáles días de la semana y dentro de cuáles horarios la campaña efectuará llamados (siempre dentro del rango de fechas establecidas en el primer paso de la creación de la campaña).



Se hace click en “Paso siguiente” y en este caso se trabaja con las “reglas de incidencia”, es decir bajo cuáles condiciones se reintentará contactar a números que dieron Ocupado, Contestador, No Contesta, Temporalmente fuera de cobertura, etc.



Como se puede observar, los campos a completar permiten determinar cada cuántos segundos debe reintentarse la comunicación y cuántas veces como máximo se debe intentar según cada estado.

Los estados telefónicos que podrán reintentarse marcar automáticamente son:
Ocupado
Contestador Automático
Destino no contesta (No atiende)
Llamada rechazada (Rechazado): cuando la llamada no pudo ser cursada por problemas inherentes a la salida telefónica.
Timeout: cuando la llamada se contactó, se conectó pero ningún agente estuvo libre como para gestionar la misma.

Se hace click en “Paso siguiente” para llegar al último paso de la creación de la campaña.



En este paso, simplemente se indican tres opciones:

Evitar duplicados: es un check que sirve para indicar al sistema que no se disque dos veces un mismo número, por más que esté dos veces en la base de contactos.
Evitar sin teléfono: es un check que sirve para indicar al sistema que no tenga en cuenta los registros de la base de contacto que no posean un teléfono principal.
Prefijo: este campo sirve para indicar al discador si debe anteponer algún prefijo delante de cada número de la base de contactos en caso que lo requiera el plan de discado de la central telefónica por donde saldrán las llamadas.


Finalmente, si se presiona el botón “Finalizar”, la campaña se termina de crear. Dependiendo de las configuraciones, el tamaño de la base de datos y el tipo de hardware donde está instalado OML este paso puede demorar varios minutos.

Reciclado de campañas con Discador
Cambio de base de contactos en campañas con Discador



6.1.3. Cambio de base de contactos en campañas finalizadas

Cuando una campaña predictiva se queda sin contactos, se puede acudir a la funcionalidad de cambio de base. Esto permite seguir operando con la misma campaña, pero renovar la fuente de contactos para que siga marcando. De esta manera se sigue el historial de reportes, grabaciones y demás estadísticas en la misma campaña.

Para llevar a cabo un cambio de base, la campaña debe estar en estado de “finalizada”. A partir de allí se indica la acción de “cambio de base” sobre la campaña en cuestión.

Esto desplegará una pantalla similar a la expuesta en la siguiente figura.







6.1.4. Reciclado de bases de contactos en campañas finalizadas
