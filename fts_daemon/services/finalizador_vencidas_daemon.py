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

import logging as _logging
import time

from django.conf import settings

from fts_daemon import locks
from fts_daemon import tasks
from fts_web.errors import FTSOptimisticLockingError
from fts_web.models import Campana


# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.services.'
                            'finalizador_vencidas_daemon')


class FinalizadorDeCampanasVencidasDaemon(object):
    """Implementa Daemon finalizador de campañas vencidas."""

    def __init__(self, max_loop=0, initial_wait=None):
        """Constructor del finalizador de campañas"""

        self.max_loop = max_loop or settings.FTS_FDCD_MAX_LOOP_COUNT

        self.initial_wait = initial_wait
        if self.initial_wait is None:
            self.initial_wait = settings.FTS_FDCD_INITIAL_WAIT

        if self.initial_wait > 0.0:
            logger.info("Realizando espera inicial de %s segs...",
                        self.initial_wait)
            time.sleep(self.initial_wait)
            logger.info("Espera inicial finalizada")

    #----------------------------------------------------------------------
    # METODOS PROXY (para faclitar unittest)
    #----------------------------------------------------------------------

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
        return Campana.objects.obtener_finalizadas()

    def _finalizar_y_programar_depuracion(self, campana):
        """Finaliza la campaña, y lanza la tarea asincrona para esperar
        a que no haya llamadas en curso y depurar la campaña.

        :returns: bool - True si se finalizo correctamente
                  False si se produjo FTSOptimisticLockingError
        """
        try:
            campana.finalizar()
        except FTSOptimisticLockingError:
            logger.warn("Se detecto FTSOptimisticLockingError. "
                        "Ignoraremos esta campana y continuaremos procesando "
                        "otras campanas",
                        exc_info=True)
            return False

        tasks.esperar_y_depurar_campana_async(campana.id)
        return True

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
            self._programar_depuracion(campana)

        #
        # Finalizacion
        #

        for campana in self._obtener_vencidas():
            logger.info("Finalizando campana %s", campana.id)
            self._finalizar_y_programar_depuracion(campana)

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


LOCK_DAEMON_FINALIZADOR_VENCIDAS = 'freetechsender/daemon-finalizador-vencidas'

if __name__ == '__main__':
    locks.lock(LOCK_DAEMON_FINALIZADOR_VENCIDAS)
    finalizador_vencidas = FinalizadorDeCampanasVencidasDaemon()
    finalizador_vencidas.run()
