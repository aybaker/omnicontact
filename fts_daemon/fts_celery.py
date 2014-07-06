# -*- coding: utf-8 -*-
"""
Puntos de entrada a metodos que pueden (y generalmente, DEBEN)
ejecutarse de manera asincrona.
"""

from __future__ import unicode_literals

import logging

from django.db import transaction
from fts_daemon import fts_celery_daemon
from fts_daemon.poll_daemon.call_status import CampanaCallStatus, \
    AsteriskCallStatus
from fts_web.models import Campana
import time


logger = logging.getLogger(__name__)


@fts_celery_daemon.app.task
def finalizar_campana(campana_id):
    """Finaliza la campaña"""
    logger.info("Se iniciara el proceso de finalizacion para la camana %s",
                campana_id)
    with transaction.atomic():
        campana = Campana.objects.get(pk=campana_id)
        if campana.estado == Campana.ESTADO_FINALIZADA:
            logger.info("Ignorando campana ya finalizada: %s", campana_id)
            return
        campana.finalizar()
        campana.procesar_finalizada()
        logger.info("La campana %s fue finalizada correctamente", campana_id)


@fts_celery_daemon.app.task
def esperar_y_finalizar_campana(campana_id):
    """Espera a que no haya llamadas en curso, y finaliza la campaña"""

    logger.info("Esperarando a que se finalicen las llamadas en curso para "
                "la campana %s", campana_id)

    while True:
        campana = Campana.objects.get(pk=campana_id)
        if campana.estado != Campana.ESTADO_ACTIVA:
            logger.info("Ignorando campana NO activa: %s", campana_id)
            return

        campana_call_status = CampanaCallStatus()
        asterisk_call_status = AsteriskCallStatus(campana_call_status)

        ok = asterisk_call_status.\
            refrescar_channel_status_si_es_posible()

        if not ok:
            logger.warn("Update de status no fue exitoso. "
                "Esperaremos y reintentaremos...")
            time.sleep(10)
            continue

        llamadas_en_curso = campana_call_status.\
            get_count_llamadas_de_campana(campana)

        if llamadas_en_curso != 0:
            logger.info("No se finalizara campana %s porque "
                "posee %s llamadas en curso. Esperaremos y "
                "reintentaremos...",
                campana.id, llamadas_en_curso)
            time.sleep(10)
            continue

        logger.info("Finalizando campana %s porque "
            "no posee llamadas en curso", campana.id)
        finalizar_campana.delay(campana_id)
