# -*- coding: utf-8 -*-
"""
Puntos de entrada a metodos para ser ejecutados de manera asincrona.

El sistema debe utilizar las funciones llamadas *_async(), para no
quedar acoplado a la herramienta usada actualmente (ej: Celery).
"""

from __future__ import unicode_literals

import logging

from fts_daemon import fts_celery_daemon
from fts_daemon.services.depurador_de_campana import (
    DepuradorDeCampanaWorkflow
)
from fts_daemon.services.esperador_para_depuracion_segura import (
    EsperadorParaDepuracionSegura
)


logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# DepuradorDeCampanaWorkflow
# -----------------------------------------------------------------------------

@fts_celery_daemon.app.task(ignore_result=True)
def depurar_campana(campana_id):
    """Depura la campaña"""
    DepuradorDeCampanaWorkflow().depurar(campana_id)


def depurar_campana_async(campana_id):
    """Depura la campaña.
    Realiza llamada asyncrona.
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
    EsperadorParaDepuracionSegura().esperar_y_depurar(campana_id)


def esperar_y_depurar_campana_async(campana_id):
    """Espera a que no haya llamadas en curso, y depura la campaña.
    Realiza llamada asyncrona.
    """
    logging.info("Lanzando servicio EsperadorParaDepuracionSegura() "
                 "en background usando Celery para campana %s", campana_id)
    return esperar_y_depurar_campana.delay(campana_id)
