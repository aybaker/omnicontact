# -*- coding: utf-8 -*-
"""
Servicio que espera hasta que no haya llamadas en curso para la campaña.
Cuando no hay llamadas en curso, entonces lanza el proceso de depuración
(de manera asíncrona).
"""

from __future__ import unicode_literals

import time

from fts_daemon.poll_daemon.call_status import CampanaCallStatus, \
    AsteriskCallStatus
from fts_web.models import Campana
import logging as _logging


logger = _logging.getLogger(__name__)


class CantidadMaximaDeIteracionesSuperada(Exception):
    pass


class EsperadorParaDepuracionSegura(object):
    """Espera hasta que no haya llamadas en curos para la campaña a finalizar,
    y cuando no haya llamadas, ejecuta su finalizacion (usando Celery).
    """

    def __init__(self, campana_call_status=None, asterisk_call_status=None):
        """Constructor

        :param campana_call_status: instancia de `CampanaCallStatus`
        :param asterisk_call_status: instancia de `AsteriskCallStatus`
        """
        self.campana_call_status = campana_call_status or CampanaCallStatus()

        self.asterisk_call_status = asterisk_call_status or \
            AsteriskCallStatus(self.campana_call_status)

        self.max_loop = 0

    def _sleep(self):
        time.sleep(10)

    def _obtener_campana(self, campana_id):
        return Campana.objects.get(pk=campana_id)

    def _depurar(self, campana_id):
        # import ciclico
        from fts_daemon.tasks import depurar_campana_async
        depurar_campana_async(campana_id)

    def _refrescar_status(self):
        return self.asterisk_call_status.\
            refrescar_channel_status_si_es_posible()

    def esperar_y_depurar(self, campana_id):
        """Espera a que no haya llamadas en curso, y depura la campaña"""

        logger.info("Esperarando a que se finalicen las llamadas en curso "
                    "para la campana %s", campana_id)

        current_loop = 0
        while True:

            if self.max_loop > 0:
                current_loop += 1
                if current_loop > self.max_loop:
                    raise(CantidadMaximaDeIteracionesSuperada())

            campana = self._obtener_campana(campana_id)
            if campana.estado == Campana.ESTADO_DEPURADA:
                logger.info("Ignorando campana ya depurada: %s", campana_id)
                return

            if campana.estado != Campana.ESTADO_FINALIZADA:
                logger.error("La campaña a procesar NO ha sido finalizada",
                             campana_id)
                return

            if not self._refrescar_status():
                logger.warn("Update de status no fue exitoso. "
                    "Esperaremos y reintentaremos...")
                self._sleep()
                continue

            llamadas_en_curso = self.campana_call_status.\
                get_count_llamadas_de_campana(campana)

            if llamadas_en_curso != 0:
                logger.info("No se depurará la campana %s porque "
                    "posee %s llamadas en curso. Esperaremos y "
                    "reintentaremos...",
                    campana.id, llamadas_en_curso)
                self._sleep()
                continue

            logger.info("Depurando campana %s porque "
                "no posee llamadas en curso", campana.id)
            self._depurar(campana_id)
            return
