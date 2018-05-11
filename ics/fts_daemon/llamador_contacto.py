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
from fts_daemon.poll_daemon.campana_tracker import DatosParaRealizarLlamada


logger = _logging.getLogger(__name__)


# FIXME: esto deberia ser un objeto / servicio


def procesar_contacto(datos_para_realizar_llamada):
    """Registra realizacion de intento (usando EventoDeContacto)
    y luego realiza ORIGINATE, registrando el resultado de dicho comando.

    :param datos_para_realizar_llamada: instancia de DatosParaRealizarLlamada

    :returns: bool - Si el originate fue exitoso (True), sino False
    """

    assert isinstance(datos_para_realizar_llamada, DatosParaRealizarLlamada)

    campana = datos_para_realizar_llamada.campana

    logger.info("Realizando originate - campana: %s - contacto: %s - "
        "numero: %s - intentos: %s", campana.id,
        datos_para_realizar_llamada.id_contacto,
        datos_para_realizar_llamada.telefono,
        datos_para_realizar_llamada.intentos)

    intento_actual = datos_para_realizar_llamada.intentos + 1

    EventoDeContacto.objects.inicia_intento(campana.id,
        datos_para_realizar_llamada.id_contacto,
        intento_actual)

    # ANTES:
    #  * Local/{contactoId}-{numberToCall}@FTS_local_campana_{campanaId}
    # AHORA:
    #  * Local/{contactoId}-{numberToCall}-{intento}@
    #                                        FTS_local_campana_{campanaId}
    channel = settings.FTS_ASTERISK_DIALPLAN_LOCAL_CHANNEL.format(
        contactoId=str(datos_para_realizar_llamada.id_contacto),
        numberToCall=str(datos_para_realizar_llamada.telefono),
        campanaId=str(campana.id),
        intento=intento_actual,
    )
    context = campana.get_nombre_contexto_para_asterisk()
    # ANTES:
    #  * fts{contactoId}
    # AHORA:
    #  * fts-{contactoId}-{numberToCall}-{intento}
    exten = settings.FTS_ASTERISK_DIALPLAN_EXTEN.format(
        contactoId=str(datos_para_realizar_llamada.id_contacto),
        numberToCall=str(datos_para_realizar_llamada.telefono),
        intento=intento_actual,
    )

    http_client_clazz = get_class(settings.FTS_ASTERISK_HTTP_CLIENT)
    http_ami_client = http_client_clazz()

    try:
        variables_de_canal = datos_para_realizar_llamada.\
            generar_variables_de_canal()

        http_ami_client.login()
        http_ami_client.originate(channel, context, exten, 1,
            (campana.segundos_ring + 2) * 1000, async=True,
            variables_de_canal=variables_de_canal)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_successful(
                campana.id,
                datos_para_realizar_llamada.id_contacto,
                intento_actual)
        return True

    except AsteriskHttpOriginateError:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, datos_para_realizar_llamada.id_contacto)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_failed(
                campana.id, datos_para_realizar_llamada.id_contacto,
                intento_actual)
        return False

    except:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, datos_para_realizar_llamada.id_contacto)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_internal_error(
                campana.id,
                datos_para_realizar_llamada.id_contacto,
                intento_actual)
        return False
