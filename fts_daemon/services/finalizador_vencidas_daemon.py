# -*- coding: utf-8 -*-
"""
Servicio encargado de chequear en la BD si hay campañas vencidas.

Campañas vencidas son las que no se procesarán, debido a la fecha fin,
o combinación de fecha fin / actuaciones.

Estas campañas son finalizadas, y luego se programa una tarea asincrona para
esperar hasta que puedan ser depuradas (por si hay llamadas en curso).

Este daemon, además, chequea si hay campañas finalizadas pendientes de ser
depurdas.
"""

from __future__ import unicode_literals

import time

from django.conf import settings
from fts_daemon.poll_daemon.call_status import AsteriskCallStatus, \
    CampanaCallStatus
from fts_web.models import Campana
import logging as _logging
from fts_daemon import tasks
from fts_web.errors import FTSOptimisticLockingError

# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.services.'
                            'finalizador_vencidas_daemon')


# @@@@@@@@@@ PENDIENTE: ARREGLAR TESTS @@@@@@@@@@


class FinalizadorDeCampanasVencidasDaemon(object):
    """Implementa Daemon finalizador de campañas vencidas."""

    def __init__(self, max_loop=0, initial_wait=None, campana_call_status=None,
        asterisk_call_status=None):
        """Constructor del finalizador de campañas
        :param campana_call_status: instancia de `CampanaCallStatus`
        :param asterisk_call_status: instancia de `AsteriskCallStatus`
        """

        self.max_loop = max_loop or settings.FTS_FDCD_MAX_LOOP_COUNT

        self.initial_wait = initial_wait
        if self.initial_wait is None:
            self.initial_wait = settings.FTS_FDCD_INITIAL_WAIT

        if self.initial_wait > 0.0:
            logger.info("Realizando espera inicial de %s segs...",
                        self.initial_wait)
            time.sleep(self.initial_wait)
            logger.info("Espera inicial finalizada")

        self.campana_call_status = campana_call_status or CampanaCallStatus()

        self.asterisk_call_status = asterisk_call_status or \
            AsteriskCallStatus(self.campana_call_status)

    #----------------------------------------------------------------------
    # METODOS PROXY (para faclitar unittest)
    #----------------------------------------------------------------------

    def _refrescar_status(self):
        """Llama a refrescar_channel_status_si_es_posible().
        Es funcion 'proxy', para facilitar unittest.
        """
        return self.asterisk_call_status.\
            refrescar_channel_status_si_es_posible()

    def _get_count_llamadas(self, campana):
        """Llama a get_count_llamadas_de_campana().
        Es funcion 'proxy', para facilitar unittest.
        """
        return self.campana_call_status.get_count_llamadas_de_campana(campana)

    def _sleep(self):
        """Realiza espera luego de finalizar el loop
        Es funcion 'proxy', para facilitar unittest.
        """
        time.sleep(settings.FTS_FDCD_LOOP_SLEEP)

    #----------------------------------------------------------------------
    # Metodos
    #----------------------------------------------------------------------

    def _obtener_vencidas(self):
        """Devuelve campañas vencidas que hay que finalizar"""
        return Campana.objects.obtener_vencidas_para_finalizar()

    def _obtener_finalizadas_por_depurar(self):
        """Devuelve campañas finalizadas pendientes de ser depuradas"""
        # @@@@@@@@@@ IMPLEMENTAR @@@@@@@@@@

    def _finalizar_y_programar_depuracion(self, campana):
        """Finaliza la campaña, y lanza la tarea asincrona para esperar
        a que no haya llamadas en curso y depurar la campaña.
        """
        try:
            campana.finalizar()
        except FTSOptimisticLockingError:
            logger.warn("Se detecto FTSOptimisticLockingError. "
                        "Ignoraremos este error y continuaremos",
                        exc_info=True)
            return

        # ANTES: tasks.finalizar_campana_async(campana.id)
        tasks.esperar_y_depurar_campana_async(campana.id)

    def _programar_depuracion(self, campana):
        """Lanza la tarea asincrona para esperar
        a que no haya llamadas en curso y depurar la campaña.
        """
        tasks.esperar_y_depurar_campana_async(campana.id)

    def _run_loop(self):
        """Ejecuta una iteración (busca campanas, las procesa)."""

        #
        # Depuracion
        #

        for campana in self._obtener_finalizadas_por_depurar():
            logger.info("Chequeando llamadas en curso para campana %s",
                        campana.id)
            self._programar_depuracion(campana)

        #
        # Finalizacion
        #

        campanas_vencidas = list(self._obtener_vencidas())

        if campanas_vencidas:
            logger.info("Obteniendo status de llamadas en curso")
            if not self._refrescar_status():
                logger.warn("No se pudo refrescar status de llamadas en "
                    "curso... Por lo tanto, no se finalizara ninguna "
                    "campana.")
                # Si no se pudo chequear status, cancelamos todo
                return

            for campana in campanas_vencidas:
                logger.info("Chequeando llamadas en curso para campana %s",
                            campana.id)
                count_llamadas_en_curso = self._get_count_llamadas(campana)

                if count_llamadas_en_curso > 0:
                    logger.info("No se finalizara la campana %s porque "
                        "hay %s llamadas en curso de dicha campana",
                        campana.id, count_llamadas_en_curso)
                    continue

                logger.info("Finalizando campana %s", campana.id)
                self._finalizar_y_programar_depuracion(campana)
        else:
            logger.info("No se encontro campana por finalizar...")

    def run(self):
        """Inicia el proceso."""

        logger.info("Iniciando daemon finalizador de campanas vencidas")

        current_loop = 1
        while True:

            self._run_loop()

            if self.max_loop > 0:
                current_loop += 1
                if current_loop > self.max_loop:
                    logger.info("max_loop alcanzado. Exit!")
                    return

            self._sleep()


if __name__ == '__main__':
    FinalizadorDeCampanasVencidasDaemon().run()
