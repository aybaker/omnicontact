# -*- coding: utf-8 -*-
"""
"""

from __future__ import unicode_literals

import logging as _logging
import signal


__all__ = ['RunningStatus',
           'set_handlers',
           'DEFAULT_SIGNALS_A_MANEJAR']


logger = _logging.getLogger(__name__)

DEFAULT_SIGNALS_A_MANEJAR = [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT]


class RunningStatus(object):
    """Mantiene bandera que indica si se debe seguir ejecutando el
    software. Esto permite realizar un shutdown controlado y ordenado
    del software.

    La instancia de este objeto esta pensado para ser compartida
    por muchas de las capas / servicios. Solo el main() detecta los signals
    y setea 'should_continue_running = False'. Todos las capas / servicios
    pueden usar este valor para saber cuando finalizar su tarea y asi permitir
    una finalizacion controlada de la ejecucion.
    """
    def __init__(self):
        self.should_continue_running = True


def _generate_signal_handler(running_status, signals_a_manejar):
    def signal_handler(signum, _):
        # OJO con lo que hacemos aca! Esta bien que generemos mensajes de log?
        # Es un signal handler, puede ejecutarse en cualquire momento...
        logger.info("signal_handler() - signal: %s", signum)
        if signum in signals_a_manejar:
            logger.info("signal_handler(): seteando continue_running = False")
            running_status.should_continue_running = False
        else:
            logger.info("signal_handler(): se ha recibido signal que NO manejamos: %s", signum)

    return signal_handler


def set_handlers(running_status, signals_a_manejar):
    """Setea los signal handlers"""
    assert isinstance(running_status, RunningStatus)
    assert len(signals_a_manejar) > 0

    signal_handler = _generate_signal_handler(running_status, signals_a_manejar)

    for a_signal in signals_a_manejar:
        logger.info("Seteando signal_handler() para signal: %s", a_signal)
        signal.signal(a_signal, signal_handler)
