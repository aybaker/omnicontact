# -*- coding: utf-8 -*-
'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import time
import datetime
import logging as _logging

# Import settings & models to force setup of Django
from django.conf import settings
from fts_web.models import Campana, IntentoDeContacto, EventoDeContacto
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

    #Fecha y Hora local de inicio de procesado de campana.
    hoy_ahora = datetime.datetime.today()
    assert (hoy_ahora.tzinfo is None)

    #Rango horario de hoy y ahora por la que se tiene que procesar la
    #campana.
    rango_horario =\
        campana.obtener_rango_horario_actuacion_en_fecha_hora(hoy_ahora)

    if not rango_horario:
        return contador_contactos

    for pendiente in campana.obtener_intentos_pendientes():
        #Hora actual local.
        hora_actual = datetime.datetime.today().time()
        assert (hora_actual.tzinfo is None)

        #Valida que la hora actual esté en rango de procesado en cada
        #pasada.
        if not rango_horario[0] <= hora_actual <= rango_horario[1]:
            return contador_contactos

        #Valida que la campana no se haya pausado.
        if Campana.objects.verifica_estado_pausada(campana.pk):
            return contador_contactos

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

    EventoDeContacto.objects.create_evento_daemon_programado(
        campana.id, pendiente.contacto.id)

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
        EventoDeContacto.objects.\
            create_evento_daemon_originate_successful(
                campana.id, pendiente.contacto.id)
    except AsteriskHttpOriginateError:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, pendiente.contacto.id)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_failed(
                campana.id, pendiente.contacto.id)
    except:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, pendiente.contacto.id)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_internal_error(
                campana.id, pendiente.contacto.id)


def main():
    logger.info("Iniciando loop: obteniendo campanas activas...")
    while True:
        campanas = Campana.objects.obtener_ejecucion()
        for campana in campanas:
            procesar_campana(campana)
        time.sleep(2)


if __name__ == '__main__':
    main()
