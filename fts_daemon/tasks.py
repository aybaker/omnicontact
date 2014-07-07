# -*- coding: utf-8 -*-
"""
Puntos de entrada a metodos que pueden (y generalmente, DEBEN)
ejecutarse de manera asincrona.
"""

from __future__ import unicode_literals

import logging

from fts_daemon import fts_celery_daemon
from fts_daemon.finalizador_de_campana.finalizadores \
    import FinalizadorDeCampanaWorkflow, EsperadorParaFinalizacionSegura


logger = logging.getLogger(__name__)


# @shared_task -- no funciono...
@fts_celery_daemon.app.task(ignore_result=True)
def finalizar_campana(campana_id):
    """Finaliza la campaña"""
    FinalizadorDeCampanaWorkflow().finalizar(campana_id)


def finalizar_campana_async(campana_id):
    """Finaliza la campaña.
    Realiza llamada asyncrona.
    """
    return finalizar_campana.delay(campana_id)


# @shared_task -- no funciono...
@fts_celery_daemon.app.task(ignore_result=True)
def esperar_y_finalizar_campana(campana_id):
    """Espera a que no haya llamadas en curso, y finaliza la campaña"""
    EsperadorParaFinalizacionSegura().esperar_y_finalizar(campana_id)


def esperar_y_finalizar_campana_async(campana_id):
    """Espera a que no haya llamadas en curso, y finaliza la campaña.
    Realiza llamada asyncrona.
    """
    return esperar_y_finalizar_campana.delay(campana_id)
