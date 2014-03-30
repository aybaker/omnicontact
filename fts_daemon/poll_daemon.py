# -*- coding: utf-8 -*-
'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import logging
import time

from fts_daemon.asterisk_ami import originate


logger = logging.getLogger("FTSenderDaemon")


def setup():
    from django.conf import settings  # @UnusedImport
    from fts_web.models import Campana  # @UnusedImport

    logging.getLogger().setLevel(logging.INFO)


def generador_de_llamadas_asterisk_dummy_factory():
    def generador_de_llamadas_asterisk(telefono):
        logger.info("GENERADOR DE LLAMADAS DUMMY -> %s", telefono)
    return generador_de_llamadas_asterisk


def generador_de_llamadas_asterisk_factory():
    """Factory de funcion que se encarga de realizar llamadas

    La funcion generada debe recibir por parametro el numero telefonico
    """
    from django.conf import settings

    def generador_de_llamadas_asterisk(telefono):
        originate(
            settings.ASTERISK['USERNAME'],
            settings.ASTERISK['PASSWORD'],
            settings.ASTERISK['HOST'],
            settings.ASTERISK['PORT'],
            settings.ASTERISK['CHANNEL_PREFIX'].format(telefono),
            settings.ASTERISK['CONTEXT'],
            settings.ASTERISK['EXTEN'],
            settings.ASTERISK['PRIORITY'],
            settings.ASTERISK['TIMEOUT']
        )
    return generador_de_llamadas_asterisk


def procesar_campana(campana, generador_de_llamadas):
    """Procesa una campana.

    Returns:
        cant_contactos_procesados
    """
    from fts_web.models import Campana, Contacto
    from django.conf import settings  # @UnusedImport

    assert isinstance(campana, Campana)
    logger.info("Iniciando procesado de campana %s", campana.id)
    contador_contactos = 0
    # for contacto in campana.bd_contacto.contactos.all():
    for contacto in campana.bd_contacto.contactos.all():
        assert isinstance(contacto, Contacto)
        logger.info(" - Realizando originate para contacto: %s", contacto.id)
        generador_de_llamadas(contacto.telefono)
        contador_contactos += 1

    logger.info("Marcando campana %s como FINALIZADA", campana.id)
    campana.finalizar()
    return contador_contactos


if __name__ == '__main__':
    logging.info("Inicianodo FTSenderDaemon...")
    setup()
    logging.info("Setup de Django OK")
    generador_de_llamadas = generador_de_llamadas_asterisk_factory()

    from fts_web.models import Campana
    while True:
        logging.info("Obteniendo campanas activas...")
        campanas = Campana.objects.obtener_activas()
        for campana in campanas:
            resultado = procesar_campana(campana, generador_de_llamadas)
        time.sleep(2)
