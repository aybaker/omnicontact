*********************************
Configuración de acceso a la PSTN
*********************************

En este capítulo vamos a explicar cómo dejar configurada la capa de *acceso a la PSTN* de OMniLeads para operar de acuerdo a los contextos planteados.
OMniLeads admite solamente SIP como tecnología de interconexión con otros conmutadores de telefonía. Por lo tanto el integrador podrá configurar troncales SIP de proveedores ITSP,
troncales SIP contra sistemas PBX y/o troncales SIP contra Gateways FXO o E1/T1.

.. important::

  A partir del **Release-1.4.0** OMniLeads implementa y recomienda el uso de troncales SIP basados en el módulo PJSIP de Asterisk, debido a su eficiencia en términos
  de recursos informáticos utilizados, así como también por el estado de *deprecated* en el cual se encuentra el módulo CHAN_SIP a partir de la versión 17 de Asterisk.

  Por lo tanto a la hora de plantear el uso de troncales SIP en esta documentación se utilizará PJSIP.
  Para disponer de la explicación de troncales utilizando chan_sip, usted podrá visitar las versiones anteriores de esta documentación.


Explicación del ABM para troncales PJSIP
*****************************************

Para acceder a la configuración debemos ingresar en el punto de menú *(Telephony -> SIP Trunks)* y allí añadir una nueva
troncal PJSIP. Se va a desplegar un formulario similar al de la figura 1.

.. image:: images/telephony_pjsiptrunk_abm.png
       :align: center

*Figure 1: New SIP Trunk*

Los campos del formulario son:

- **Trunk Name**: el nombre del troncal. Debe ser alfanumperico sin espacios ni caracteres especiales (Ej: Trunk_provider_a).
- **Number of channels**: es la cantidad de canales que permite el vínculo.
- **Caller id**: el número con el que saldrán las llamadas por el troncal.
- **SIP details**: en este campo de texto se proporcionan los parámetros SIP usando sintaxis de `PJSIP configuration Wizard <https://wiki.asterisk.org/wiki/display/AST/PJSIP+Configuration+Wizard>`_ de Asterisk.

Como se puede apreciar en la figura 1, existen una serie de *plantillas* de configuración en base al tipo de conexión troncal que se desea configurar, que pueden
facilitar bastante el trabajo de configuración  .

A continuación desplegamos las plantillas sugeridas para los tipos de escenarios planteados como casos de uso típicos de OMniLeads.

.. toctree::
  :maxdepth: 1

  telephony_pjsip_templates.rst

Configuración para el enrutamiento de llamadas salientes
********************************************************

OMniLeads permite gestionar el enrutamiento de llamadas salientes sobre múltiples troncales SIP (previamente creados), de manera tal que
utilizando criterios como el *largo o prefijo del número* para determinar por qué vínculo SIP encaminar la llamada. Además es posible mantener una lógica de *failover*
entre los diferentes troncales SIP asignados a una ruta saliente.

Para acceder a la vista de configuración de rutas salientes, ingresar al punto de menú (*Telephony -> Outbound routes*)

.. image:: images/telephony_outr.png

*Figure 2: Outbound route*

- **Nombre**: es el nombre de la ruta (alfanumérico sin espacios)
- **Ring time**: es el tiempo (en segundos) que las llamadas cursadas por esta ruta, intentarán establecer una conexión con el destino, antes de seguir intentando por el próximo troncal o bien descartar la llamada.
- **Dial options**: son las opciones de la aplicación "Dial" utilizadas por Asterisk(r) en bajo nivel.
- **Patrones de discado**: mediante patrones, se puede representar los *tipos de llamadas* que serán aceptadas por la ruta y así entonces colocadas sobre el Troncal SIP para finalmente alcanzar el destino deseado.

Para comprender cómo se representan los dígitos utilizando *patrones*, se recomienda leer éste link: https://www.voip-info.org/asterisk-extension-matching/.

Dentro de cada patrón ingresado hay tres campos:


  * **Prepend**: son los dígitos que se mandan por el trunk SIP como adicionales al número discado. Es decir llegan al Trunk posicionados delante del número marcado.
  * **Prefijo**: son los dígitos que pueden venir como “prefijo” de una llamada marcada y éstos serán quitados en el momento de enviarlos por el SIP Trunk.
  * **Patrón de discado**: se busca representar en este campo el patrón de dígitos autorizados que la ruta va a procesar para y enviar a un SIP Trunk para sacar la llamada hacia el exterior.

- **Secuencia de troncales**: son los troncales SIP sobre los cuales la ruta saliente va a intentar establecer la llamada discada por OML. Si la llamada falla en un troncal, se sigue intentando en el siguiente.

Configuración de enrutamiento de llamadas entrantes
****************************************************

El tratamiento de llamadas entrantes se abordará en la sección *Campañas Entrantes* de esta documentación ya que para poder operar con dicho módulo debemos al menos
tener creado algún objeto (IVR, condicional de tiempo, campaña entrante, etc.) hacia a donde rutear cada DID generado.

:ref:`about_inboundroutes`.
