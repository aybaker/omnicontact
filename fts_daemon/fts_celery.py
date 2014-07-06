# -*- coding: utf-8 -*-
"""
Puntos de entrada a metodos que pueden (y generalmente, DEBEN)
ejecutarse de manera asincrona.
"""

from __future__ import unicode_literals

import logging

from django.db import transaction
from fts_daemon import fts_celery_daemon
from fts_web.models import Campana


logger = logging.getLogger(__name__)


@fts_celery_daemon.app.task
def finalizar_campana(campana_id):
    """Finaliza la campaña"""
    logger.info("Se iniciara el proceso de finalizacion para la camana %s",
                campana_id)
    with transaction.atomic():
        campana = Campana.objects.get(pk=campana_id)
        campana.finalizar()
        campana.procesar_finalizada()
        logger.info("La campana %s fue finalizada correctamente", campana_id)
