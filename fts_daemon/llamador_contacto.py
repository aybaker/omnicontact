# -*- coding: utf-8 -*-
"""
Realiza el procesamiento para contactar a 1 contacto.

Usado por el daemon enviador.
"""

from __future__ import unicode_literals

from django.conf import settings
from fts_daemon.asterisk_ami_http import AsteriskHttpOriginateError
from fts_web.models import EventoDeContacto
from fts_web.utiles import get_class
import logging as _logging


logger = _logging.getLogger(__name__)


def procesar_contacto(campana, contacto_id, numero):
    """Registra realizacion de intento (usando EventoDeContacto)
    y luego realiza ORIGINATE, registrando el resultado de dicho comando.
    """

    logger.info("Realizando originate - campana: %s - contacto: %s - "
        "numero: %s", campana.id, contacto_id, numero)

    EventoDeContacto.objects.inicia_intento(campana.id, contacto_id)

    # Local/{contactoId}-{numberToCall}@FTS_local_campana_{campanaId}
    channel = settings.ASTERISK['LOCAL_CHANNEL'].format(
        contactoId=str(contacto_id),
        numberToCall=str(numero),
        campanaId=str(campana.id),
    )
    context = campana.get_nombre_contexto_para_asterisk()
    exten = settings.ASTERISK['EXTEN'].format(
        contactoId=str(contacto_id),
    )

    http_client_clazz = get_class(settings.FTS_ASTERISK_HTTP_CLIENT)
    http_ami_client = http_client_clazz()

    try:
        http_ami_client.login()
        http_ami_client.originate(channel, context, exten, 1,
            (campana.segundos_ring + 2) * 1000, async=True)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_successful(
                campana.id, contacto_id)
    except AsteriskHttpOriginateError:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, contacto_id)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_failed(
                campana.id, contacto_id)
    except:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, contacto_id)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_internal_error(
                campana.id, contacto_id)
