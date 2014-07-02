# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

import time

from django.conf import settings
from fts_daemon.poll_daemon.call_status import AsteriskCallStatus,\
    CampanaCallStatus
from fts_web.models import Campana
import logging as _logging


# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.finalizador_vencidas_daemon.main')


# TODO: transformar en objeto, para facilitar testing
def main(max_loop=0, initial_wait=0.0, campana_call_status=None,
    asterisk_call_status=None, obtener_vencidas_func=None):
    """Funcion main() para daemon finalizador. Recibe por parametro
    las dependencias para facilitar el testing.

    :param campana_call_status: instancia de `CampanaCallStatus`
    :param asterisk_call_status: instancia de `AsteriskCallStatus`
    :param obtener_vencidas_func: funcion a llamar que devuelve campanas
                                  vencidas. Por default usamos
                                  `Campana.objects.
                                  obtener_vencidas_para_finalizar()`.
    """
    logger.info("Iniciando daemon finalizador de campanas vencidas")
    max_loop = max_loop or settings.FTS_FDCD_MAX_LOOP_COUNT
    initial_wait = initial_wait or settings.FTS_FDCD_INITIAL_WAIT

    if initial_wait > 0.0:
        logger.info("Realizando espera inicial de %s segs...", initial_wait)
        time.sleep(initial_wait)
        logger.info("Espera inicial finalizada")

    if campana_call_status is None:
        campana_call_status = CampanaCallStatus()

    if asterisk_call_status is None:
        asterisk_call_status = AsteriskCallStatus(campana_call_status)

    if obtener_vencidas_func is None:
        obtener_vencidas_func = Campana.objects.\
            obtener_vencidas_para_finalizar

    current_loop = 1
    while True:
        logger.info("Obteniendo status de llamadas en curso")
        updt_ok = asterisk_call_status.refrescar_channel_status_si_es_posible()

        if updt_ok:
            # El status se actualizo! Avanzamos...
            for campana in obtener_vencidas_func():
                count_llamadas_en_curso = campana_call_status.\
                    get_count_llamadas_de_campana(campana)

                if count_llamadas_en_curso > 0:
                    logger.info("No se finalizara la campana %s porque hay "
                        "%s llamadas en curso de dicha campana",
                        campana.id, count_llamadas_en_curso)
                else:
                    logger.info("Finalizando campana %s", campana.id)
                    campana.finalizar()
            else:
                logger.info("No hay campanas por finalizar...")
        else:
            logger.warn("No se pudo refrescar status de llamadas en curso... "
                "Por lo tanto, no se finalizara ninguna campana")

        if max_loop > 0:
            current_loop += 1
            if current_loop > max_loop:
                logger.info("max_loop alcanzado. Exit!")
                return

        time.sleep(settings.FTS_FDCD_LOOP_SLEEP)

if __name__ == '__main__':
    main()
