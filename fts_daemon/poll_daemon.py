# -*- coding: utf-8 -*-
'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import time
import logging as _logging

# Import settings & models to force setup of Django
from django.conf import settings
from fts_web.models import Campana, IntentoDeContacto
from fts_web.utiles import get_class
from fts_daemon.asterisk_ami_http import AsteriskHttpOriginateError

# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.poll_daemon')


def procesar_campana(campana):
    """Procesa una campana (no chequea su estado, se suponque que
    la campaña esta en el estado correcto).

    El procesado incluye: buscar intentos de envios pendientes e
    intentar la llamadas.

    Una vez que se procesaro tondos los intentos pendientes, se
    marca la campaña como finalizada.

    Returns:
        cant_contactos_procesados
    """
    assert isinstance(campana, Campana)
    logger.info("Iniciando procesado de campana %s", campana.id)
    contador_contactos = 0

    for pendiente in campana.obtener_intentos_pendientes():
        procesar_contacto(pendiente, campana)
        contador_contactos += 1
    else:
        logger.info("Marcando campana %s como FINALIZADA", campana.id)
        campana.finalizar()

    return contador_contactos


def procesar_contacto(pendiente, campana):
    assert isinstance(pendiente, IntentoDeContacto)
    logger.info("Realizando originate para IntentoDeContacto %s",
        pendiente.id)

    # Local/{callId}-{numberToCall}@FTS_local_campana_{campanaId}
    channel = settings.ASTERISK['LOCAL_CHANNEL'].format(
        callId=str(pendiente.id),
        numberToCall=str(pendiente.contacto.telefono),
        campanaId=str(campana.id),
    )
    context = campana.get_nombre_contexto_para_asterisk()
    exten = settings.ASTERISK['EXTEN'].format(
        callId=str(pendiente.id),
    )

    http_client_clazz = get_class(settings.FTS_ASTERISK_HTTP_CLIENT)
    http_ami_client = http_client_clazz()
    try:
        http_ami_client.login()
        http_ami_client.originate(channel, context, exten, 1,
            (campana.segundos_ring + 2) * 1000, async=True)
        originate_ok = True
    except AsteriskHttpOriginateError:
        originate_ok = False
        logger.exception("Originate failed")

    IntentoDeContacto.objects.update_estado_por_originate(pendiente.id,
        originate_ok)


def main():
    logger.info("Iniciando loop: obteniendo campanas activas...")
    while True:
        campanas = Campana.objects.obtener_ejecucion()
        for campana in campanas:
            procesar_campana(campana)
        time.sleep(2)


if __name__ == '__main__':
    main()
