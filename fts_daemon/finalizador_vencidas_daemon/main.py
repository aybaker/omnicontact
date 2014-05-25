# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

import time

from django.conf import settings
from fts_web.models import Campana
import logging as _logging


# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.finalizador_vencidas_daemon.main')


def main(max_loop=0, initial_wait=0.0):
    logger.info("Iniciando daemon finalizador de campanas vencidas")
    max_loop = max_loop or settings.FTS_FDCD_MAX_LOOP_COUNT
    initial_wait = initial_wait or settings.FTS_FDCD_INITIAL_WAIT

    if initial_wait > 0.0:
        logger.info("Realizando espera inicial de %s segs...", initial_wait)
        time.sleep(initial_wait)
        logger.info("Espera inicial finalizada")

    current_loop = 1
    while True:
        logger.info("Iniciando Campana.objects.finalizar_vencidas()")
        Campana.objects.finalizar_vencidas()

        if max_loop > 0:
            current_loop += 1
            if current_loop > max_loop:
                logger.info("max_loop alcanzado. Exit!")
                return

        time.sleep(settings.FTS_FDCD_LOOP_SLEEP)

if __name__ == '__main__':
    main()
