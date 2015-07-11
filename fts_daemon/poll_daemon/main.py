# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

import os
import time
import signal
import sys

import logging as _logging

from django.conf import settings

from fts_daemon.poll_daemon.scheduler import Llamador, RunningStatus


# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.poll_daemon.main')


def _dump_settings():
    names = [name for name in dir(settings) if name.find('FTS') >= 0]
    for name in names:
        logger.info(" + %s: '%s'", name, getattr(settings, name))


def main(max_loop=0, initial_wait=0.0):
    logger.info("Iniciando poll daemon")
    logger.info("Dump de configuracion")
    _dump_settings()
    FTS_MAX_LOOPS = int(os.environ.get("FTS_MAX_LOOPS", max_loop))
    FTS_INITIAL_WAIT = float(os.environ.get("FTS_INITIAL_WAIT", initial_wait))
    if FTS_INITIAL_WAIT > 0.0:
        logger.info("Iniciando espera inicial de %s segs...", FTS_INITIAL_WAIT)
        time.sleep(FTS_INITIAL_WAIT)
        logger.info("Espera inicial finalizada")

    # Acomodamos signal handler, justo antes de iniciar
    signals_a_manejar = [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT]
    running_status = RunningStatus()

    def signal_handler(signum, _):
        logger.info("signal_handler() - signal: %s", signum)
        if signum in signals_a_manejar:
            logger.info("signal_handler(): seteando continue_running = False")
            running_status.should_continue_running = False
            if not running_status.working:
                # No se estaba trabajando, asi que podemos salir directamente
                sys.exit(0)
        else:
            logger.info("signal_handler(): se ha recibido signal que NO manejamos: %s", signum)

    for a_signal in signals_a_manejar:
        logger.info("Seteando signal_handler() para signal: %s", a_signal)
        signal.signal(a_signal, signal_handler)

    Llamador().run(max_loops=FTS_MAX_LOOPS,
                   running_status=running_status)


if __name__ == '__main__':
    main()
