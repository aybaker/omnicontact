# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

import os
import time
import signal

import logging as _logging

import django
from django.conf import settings

# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.poll_daemon.main')


LOCK_DAEMON_LLAMADOR = 'freetechsender/daemon-llamador'


def _dump_settings():
    names = [name for name in dir(settings) if name.find('FTS') >= 0]
    for name in names:
        logger.info(" + %s: '%s'", name, getattr(settings, name))


def main(max_loop=0, initial_wait=0.0):
    django.setup()
    
    logger.info("Iniciando poll daemon")

    # Realizamos *import* aqui porque necesitamos que ANTES
    #  se haya llamado a *django.setup()*
    from fts_daemon import locks
    from fts_daemon import main_utils
    from fts_daemon.poll_daemon.scheduler import Llamador

    logger.info("Dump de configuracion")
    _dump_settings()

    locks.lock(LOCK_DAEMON_LLAMADOR)

    FTS_MAX_LOOPS = int(os.environ.get("FTS_MAX_LOOPS", max_loop))
    FTS_INITIAL_WAIT = float(os.environ.get("FTS_INITIAL_WAIT", initial_wait))
    if FTS_INITIAL_WAIT > 0.0:
        logger.info("Iniciando espera inicial de %s segs...", FTS_INITIAL_WAIT)
        time.sleep(FTS_INITIAL_WAIT)
        logger.info("Espera inicial finalizada")

    # Acomodamos signal handler, justo antes de iniciar
    running_status = main_utils.RunningStatus()
    main_utils.set_handlers(running_status,
                            [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT])

    llamador = Llamador(running_status=running_status)
    llamador.run(max_loops=FTS_MAX_LOOPS,)


if __name__ == '__main__':
    main()
