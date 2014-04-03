# -*- coding: utf-8 -*-
'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import logging as _logging
import time

from fts_daemon.asterisk_ami import originate


FORMAT = "%(asctime)-15s [%(levelname)7s] %(name)20s - %(message)s"

logger = _logging.getLogger("FTSDaemon")


def setup():
    from django.conf import settings  # @UnusedImport
    from fts_web.models import Campana  # @UnusedImport
    # _logging.getLogger().setLevel(_logging.INFO)


class FtsDaemonCallIdGenerator(object):
    """Genera ID para identificar llamadas"""

    def __init__(self):
        self.last = int(time.time())

    def gen(self):
        self.last += 1
        return self.last

FTS_DAEMON_CALL_ID_GENERATOR = FtsDaemonCallIdGenerator()


def generador_de_llamadas_asterisk_dummy_factory():
    def generador_de_llamadas_asterisk(telefono, call_id):
        logger.info("GENERADOR DE LLAMADAS DUMMY -> %s", telefono)
    return generador_de_llamadas_asterisk


def generador_de_llamadas_asterisk_factory():
    """Factory de funcion que se encarga de realizar llamadas

    La funcion generada debe recibir por parametro:
        a) el numero telefonico
        b) [OPCIONAL] un identificador UNICO para la llamada
    """
    from django.conf import settings

    def generador_de_llamadas_asterisk(telefono, callid=None):
        if callid is None:
            callid = FTS_DAEMON_CALL_ID_GENERATOR.gen()
        originate(
            settings.ASTERISK['USERNAME'],
            settings.ASTERISK['PASSWORD'],
            settings.ASTERISK['HOST'],
            settings.ASTERISK['PORT'],
            settings.ASTERISK['CHANNEL_PREFIX'].format(telefono),
            settings.ASTERISK['CONTEXT'],
            settings.ASTERISK['EXTEN'].format(callid),
            settings.ASTERISK['PRIORITY'],
            settings.ASTERISK['TIMEOUT']
        )
    return generador_de_llamadas_asterisk


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
    from django.conf import settings  # @UnusedImport

    assert isinstance(campana, Campana)
    logger.info("Iniciando procesado de campana %s", campana.id)
    contador_contactos = 0
    
    for pendiente in campana.obtener_intentos_pendientes():
        assert isinstance(pendiente, IntentoDeContacto)
        logger.info(" - Realizando originate para IntentoDeContacto %s",
            pendiente.id)
        generador_de_llamadas(pendiente.contacto.telefono, pendiente.id)
        contador_contactos += 1

    logger.info("Marcando campana %s como FINALIZADA", campana.id)
    campana.finalizar()
    return contador_contactos


if __name__ == '__main__':
    _logging.basicConfig(level=_logging.INFO, format=FORMAT)
    logger.info("Inicianodo FTSenderDaemon...")
    setup()
    logger.info("Setup de Django OK")
    generador_de_llamadas = generador_de_llamadas_asterisk_factory()

    from fts_web.models import Campana
    while True:
        logger.info("Obteniendo campanas activas...")
        campanas = Campana.objects.obtener_activas()
        for campana in campanas:
            resultado = procesar_campana(campana, generador_de_llamadas)
        time.sleep(2)
