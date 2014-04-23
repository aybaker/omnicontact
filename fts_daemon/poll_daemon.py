# -*- coding: utf-8 -*-
'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import time

import logging as _logging


logger = _logging.getLogger('poll_daemon')


def setup():
    from django.conf import settings  # @UnusedImport
    from fts_web.models import Campana  # @UnusedImport


def procesar_campana(campana, generador_de_llamadas):
    """Procesa una campana (no chequea su estado, se suponque que
    la campaña esta en el estado correcto).

    El procesado incluye: buscar intentos de envios pendientes e
    intentar la llamadas.

    Una vez que se procesaro tondos los intentos pendientes, se
    marca la campaña como finalizada.

    Returns:
        cant_contactos_procesados
    """
    from fts_web.models import Campana, IntentoDeContacto

    assert isinstance(campana, Campana)
    logger.info("Iniciando procesado de campana %s", campana.id)
    contador_contactos = 0

    for pendiente in campana.obtener_intentos_pendientes():
        assert isinstance(pendiente, IntentoDeContacto)
        logger.info("Realizando originate para IntentoDeContacto %s",
            pendiente.id)
        context = campana.get_nombre_contexto_para_asterisk()
        res = generador_de_llamadas(pendiente.contacto.telefono, pendiente.id,
            context)

        IntentoDeContacto.objects.update_resultado_si_corresponde(
            pendiente.id, res)

        contador_contactos += 1
    else:
        logger.info("Marcando campana %s como FINALIZADA", campana.id)
        campana.finalizar()

    return contador_contactos


if __name__ == '__main__':
    logger.info("Inicianodo FTSenderDaemon...")
    setup()
    logger.info("Setup de Django OK")

    from fts_daemon.asterisk_originate import generador_de_llamadas_asterisk_factory
    from fts_web.models import Campana

    generador_de_llamadas = generador_de_llamadas_asterisk_factory()

    logger.info("Iniciando loop: obteniendo campanas activas...")
    while True:
        campanas = Campana.objects.obtener_activas()
        for campana in campanas:
            procesar_campana(campana, generador_de_llamadas)
        time.sleep(2)
