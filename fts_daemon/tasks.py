# -*- coding: utf-8 -*-
"""
Puntos de entrada a metodos para ser ejecutados de manera asincrona.

El sistema debe utilizar las funciones llamadas *_async(), para no
quedar acoplado a la herramienta usada actualmente (ej: Celery).
"""

from __future__ import unicode_literals

import logging
import time

from fts_daemon import fts_celery_daemon
from fts_daemon import locks
from fts_daemon.services.depurador_de_campana import (
    DepuradorDeCampanaWorkflow
)
from fts_daemon.services.esperador_para_depuracion_segura import (
    EsperadorParaDepuracionSegura
)


logger = logging.getLogger(__name__)


LOCK_DEPURACION_DE_CAMPANA = 'freetechsender.depurador.de.campana'


def _internal_command(campana_id):
    """
    :param campana_id:
    :return: boolean, indica si se ha detectado y ejecutado un comando valido
    """
    logging.info("_internal_command(): '%s'", campana_id)

    if campana_id.startswith('SLEEP_'):
        sleep_time = float(campana_id.split('_')[1])
        logger.info("Iniciando espera de %s segundos", sleep_time)
        time_fin = time.time() + sleep_time
        while time.time() < time_fin:
            logger.info("Esperando...")
            time.sleep(1)
        logger.info("Espera de %s segundos finalizada", sleep_time)
        return True
    else:
        logging.info("_internal_command() desconocido: '%s'", campana_id)
        return False




# -----------------------------------------------------------------------------
# DepuradorDeCampanaWorkflow
# -----------------------------------------------------------------------------

@fts_celery_daemon.app.task(ignore_result=True)
def depurar_campana(campana_id):
    """Depura la campaña"""

    locks.lock(LOCK_DEPURACION_DE_CAMPANA)

    if isinstance(campana_id, (str, unicode)):
        if _internal_command(campana_id):
            return

    DepuradorDeCampanaWorkflow().depurar(campana_id)


def depurar_campana_async(campana_id):
    """Depura la campaña.

    Realiza la llamada asyncrona y devuelve el control inmediatamente.
    """
    logging.info("Lanzando servicio DepuradorDeCampanaWorkflow() "
                 "en background usando Celery para campana %s", campana_id)
    return depurar_campana.delay(campana_id)


# -----------------------------------------------------------------------------
# EsperadorParaDepuracionSegura
# -----------------------------------------------------------------------------

@fts_celery_daemon.app.task(ignore_result=True)
def esperar_y_depurar_campana(campana_id):
    """Espera a que no haya llamadas en curso, y depura la campaña"""

    if isinstance(campana_id, (str, unicode)):
        if _internal_command(campana_id):
            return

    EsperadorParaDepuracionSegura().esperar_y_depurar(campana_id)


def esperar_y_depurar_campana_async(campana_id):
    """Espera a que no haya llamadas en curso, y depura la campaña.

    Realiza la llamada asyncrona y devuelve el control inmediatamente.
    """
    logging.info("Lanzando servicio EsperadorParaDepuracionSegura() "
                 "en background usando Celery para campana %s", campana_id)
    return esperar_y_depurar_campana.delay(campana_id)
