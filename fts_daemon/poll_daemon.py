# -*- coding: utf-8 -*-
from __future__ import unicode_literals

'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''
import logging
import time


logger = logging.getLogger("FTSenderDaemon")


def setup():
    from django.conf import settings
    from fts_web.models import Campana
    logging.getLogger().setLevel(logging.INFO)


def procesar_campana(campana):
    """Procesa una campana.

    Returns:
        cant_contactos_procesados
    """
    from fts_web.models import Campana
    assert isinstance(campana, Campana)
    logger.info("Iniciando procesado de campana %s", campana.id)
    contador_contactos = 0
    for contacto in campana.bd_contacto.contactos.all():
        logger.info(" - Procesando contacto %s", contacto.id)
        contador_contactos += 1

    logger.info("Marcando cmapana %s como FINALIZADA", campana.id)
    campana.finalizar()
    return contador_contactos


if __name__ == '__main__':
    logging.info("Inicianodo FTSenderDaemon...")
    setup()
    logging.info("Setup de Django OK")
    from fts_web.models import Campana
    while True:
        logging.info("Obteniendo campanas activas...")
        campanas = Campana.objects.obtener_activas()
        for campana in campanas:
            resultado = procesar_campana(campana)
        time.sleep(2)
