# -*- coding: utf-8 -*-
"""
Realiza el procesamiento para contactar a 1 contacto.

Usado por el daemon enviador.
"""

from __future__ import unicode_literals

from django.conf import settings
from fts_daemon.asterisk_ami_http import AsteriskHttpOriginateError
from fts_daemon.models import EventoDeContacto
from fts_web.utiles import get_class
import logging as _logging


logger = _logging.getLogger(__name__)


# FIXME: esto deberia ser un objeto / servicio


def procesar_contacto(datos_para_realizar_llamada):
    """Registra realizacion de intento (usando EventoDeContacto)
    y luego realiza ORIGINATE, registrando el resultado de dicho comando.

    :param campana: campaña a la que pertenece el contacto
    :param contacto_id: id de contacto
    :param numero: el numero al cual hay que llamar
    :param cant_intentos: cantidad de intentos que ya fueron realizado
    :returns: bool - Si el originate fue exitoso (True), sino False
    """

    # FTS-306 - @hgdeoro - FIXME: ELIMINAR ESTA EXPANSION DE LOS DATOS DE datos_para_realizar_llamada
    campana, contacto_id, numero, cant_intentos = datos_para_realizar_llamada

    logger.info("Realizando originate - campana: %s - contacto: %s - "
        "numero: %s - intentos: %s", campana.id, contacto_id, numero,
        cant_intentos)

    intento_actual = cant_intentos + 1

    EventoDeContacto.objects.inicia_intento(campana.id, contacto_id,
        intento_actual)

    # ANTES:
    #  * Local/{contactoId}-{numberToCall}@FTS_local_campana_{campanaId}
    # AHORA:
    #  * Local/{contactoId}-{numberToCall}-{intento}@
    #                                        FTS_local_campana_{campanaId}
    channel = settings.FTS_ASTERISK_DIALPLAN_LOCAL_CHANNEL.format(
        contactoId=str(contacto_id),
        numberToCall=str(numero),
        campanaId=str(campana.id),
        intento=intento_actual,
    )
    context = campana.get_nombre_contexto_para_asterisk()
    # ANTES:
    #  * fts{contactoId}
    # AHORA:
    #  * fts-{contactoId}-{numberToCall}-{intento}
    exten = settings.FTS_ASTERISK_DIALPLAN_EXTEN.format(
        contactoId=str(contacto_id),
        numberToCall=str(numero),
        intento=intento_actual,
    )

    http_client_clazz = get_class(settings.FTS_ASTERISK_HTTP_CLIENT)
    http_ami_client = http_client_clazz()

    try:
        http_ami_client.login()
        http_ami_client.originate(channel, context, exten, 1,
            (campana.segundos_ring + 2) * 1000, async=True)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_successful(
                campana.id, contacto_id, intento_actual)
        return True
    except AsteriskHttpOriginateError:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, contacto_id)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_failed(
                campana.id, contacto_id, intento_actual)
        return False
    except:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, contacto_id)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_internal_error(
                campana.id, contacto_id, intento_actual)
        return False
