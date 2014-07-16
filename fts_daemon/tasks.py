# -*- coding: utf-8 -*-
"""
Puntos de entrada a metodos que pueden (y generalmente, DEBEN)
ejecutarse de manera asincrona.

El sistema debe utilizar las funciones llamadas *_async(), para no
quedar acoplado a la herramienta usada actualmente (ej: Celery).
"""

from __future__ import unicode_literals

import logging

from fts_daemon import fts_celery_daemon
from fts_daemon.services.depurador_de_campana import (
    DepuradorDeCampanaWorkflow, EsperadorParaFinalizacionSegura)


logger = logging.getLogger(__name__)

# @@@@@@@@@@ EVITAR RE-PROGRAMAR TAREAS @@@@@@@@@@
# O sea, si ya hay una tarea (encolada o ejecutandose) para esta
# campaña, entonces NO deberiamos hacer nada!
# Un cache local NO sirve, porque por ahi se programó, pero
# por algun problema no se procesó. Por esto hay que ir a la fuente,
# a Celery (queues y/o workers)


# @shared_task -- no funciono...
@fts_celery_daemon.app.task(ignore_result=True)
def depurar_campana(campana_id):
    """Depura la campaña"""
    # EX: finalizar_campana(campana_id)
    DepuradorDeCampanaWorkflow().finalizar(campana_id)


def depurar_campana_async(campana_id):
    """Depura la campaña.
    Realiza llamada asyncrona.
    """
    # EX: finalizar_campana_async(campana_id)
    return depurar_campana.delay(campana_id)


# @shared_task -- no funciono...
@fts_celery_daemon.app.task(ignore_result=True)
def esperar_y_depurar_campana(campana_id):
    """Espera a que no haya llamadas en curso, y depura la campaña"""
    # EX: esperar_y_finalizar_campana(campana_id)
    EsperadorParaFinalizacionSegura().esperar_y_finalizar(campana_id)


def esperar_y_depurar_campana_async(campana_id):
    """Espera a que no haya llamadas en curso, y depura la campaña.
    Realiza llamada asyncrona.
    """
    # EX: esperar_y_finalizar_campana_async(campana_id)
    return esperar_y_depurar_campana.delay(campana_id)
