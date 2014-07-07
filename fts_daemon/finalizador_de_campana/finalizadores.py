# -*- coding: utf-8 -*-
"""
Componentes encargados del finalizado de Campañas.
"""

from __future__ import unicode_literals

import time

from django.db import transaction
from fts_daemon.models import EventoDeContacto
from fts_daemon.poll_daemon.call_status import CampanaCallStatus, \
    AsteriskCallStatus
from fts_web.models import Campana
import logging as _logging


logger = _logging.getLogger(__name__)


class FinalizadorDeCampanaWorkflow(object):
    """Realiza los chequeos y pasos necesarios para finalizar una campaña.
    El metodo `finalizar()` debe ser llamddo, y pasar el ID de la campaña
    a finalizar por parametro."""

    def _obtener_campana(self, campana_id):
        return Campana.objects.get(pk=campana_id)

    def finalizar(self, campana_id):
        logger.info("Se iniciara el proceso de finalizacion para la camana %s",
                    campana_id)

        with transaction.atomic():

            campana = self._obtener_campana(campana_id)
            if campana.estado == Campana.ESTADO_FINALIZADA:
                logger.info("Ignorando campana ya finalizada: %s", campana_id)
                return

            campana.recalcular_aedc_completamente()
            campana.finalizar()

            # campana.procesar_finalizada()
            campana.crea_reporte_csv()
            EventoDeContacto.objects.depurar_eventos_de_contacto(campana.id)

        # Fuera de la TX, logueamos OK (por si se produce un error
        # al realizar commit)
        logger.info("La campana %s fue finalizada correctamente",
                    campana_id)


class CantidadMaximaDeIteracionesSuperada(Exception):
    pass


class EsperadorParaFinalizacionSegura(object):
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

    def _finalizar(self, campana_id):
        # import ciclico
        from fts_daemon.tasks import finalizar_campana_async
        finalizar_campana_async(campana_id)

    def _refrescar_status(self):
        return self.asterisk_call_status.\
            refrescar_channel_status_si_es_posible()

    def esperar_y_finalizar(self, campana_id):
        """Espera a que no haya llamadas en curso, y finaliza la campaña"""

        logger.info("Esperarando a que se finalicen las llamadas en curso "
                    "para la campana %s", campana_id)

        current_loop = 0
        while True:

            if self.max_loop > 0:
                current_loop += 1
                if current_loop > self.max_loop:
                    raise(CantidadMaximaDeIteracionesSuperada())

            campana = self._obtener_campana(campana_id)
            if campana.estado == Campana.ESTADO_FINALIZADA:
                logger.info("Ignorando campana finalizada: %s", campana_id)
                return

            if not self._refrescar_status():
                logger.warn("Update de status no fue exitoso. "
                    "Esperaremos y reintentaremos...")
                self._sleep()
                continue

            llamadas_en_curso = self.campana_call_status.\
                get_count_llamadas_de_campana(campana)

            if llamadas_en_curso != 0:
                logger.info("No se finalizara campana %s porque "
                    "posee %s llamadas en curso. Esperaremos y "
                    "reintentaremos...",
                    campana.id, llamadas_en_curso)
                self._sleep()
                continue

            logger.info("Finalizando campana %s porque "
                "no posee llamadas en curso", campana.id)
            self._finalizar(campana_id)
            return
