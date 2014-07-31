# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

import os
import time

from fts_daemon.poll_daemon.scheduler import Llamador
import logging as _logging
from django.conf import settings


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
    Llamador().run(max_loops=FTS_MAX_LOOPS)


if __name__ == '__main__':
    main()
