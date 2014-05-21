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


def main(max_loop=0, initial_wait=0.0):
    logger.info("Iniciando poll daemon")
    logger.info("Dump de configuracion")
    logger.info(" + FTS_ASTERISK_DIALPLAN_LOCAL_CHANNEL: '%s'",
        settings.FTS_ASTERISK_DIALPLAN_LOCAL_CHANNEL)
    logger.info(" + FTS_ASTERISK_DIALPLAN_EXTEN: '%s'",
        settings.FTS_ASTERISK_DIALPLAN_EXTEN)
    logger.info(" + FTS_ASTERISK_DIALPLAN_PRIORITY: '%s'",
        settings.FTS_ASTERISK_DIALPLAN_PRIORITY)
    logger.info(" + FTS_DIALPLAN_FILENAME: '%s'",
        settings.FTS_DIALPLAN_FILENAME)
    logger.info(" + FTS_QUEUE_FILENAME: '%s'",
        settings.FTS_QUEUE_FILENAME)
    logger.info(" + FTS_RELOAD_CMD: '%s'",
        settings.FTS_RELOAD_CMD)
    logger.info(" + TMPL_FTS_AUDIO_CONVERSOR: '%s'",
        settings.TMPL_FTS_AUDIO_CONVERSOR)
    logger.info(" + TMPL_FTS_AUDIO_CONVERSOR_EXTENSION: '%s'",
        settings.TMPL_FTS_AUDIO_CONVERSOR_EXTENSION)
    logger.info(" + FTS_ASTERISK_CONFIG_CHECK_AUDIO_FILE_EXISTS: '%s'",
        settings.FTS_ASTERISK_CONFIG_CHECK_AUDIO_FILE_EXISTS)
    logger.info(" + FTS_FAST_AGI_DAEMON_PROXY_URL: '%s'",
        settings.FTS_FAST_AGI_DAEMON_PROXY_URL)
    logger.info(" + FTS_FAST_AGI_DAEMON_BIND: '%s'",
        settings.FTS_FAST_AGI_DAEMON_BIND)
    logger.info(" + FTS_DAEMON_SLEEP_SIN_TRABAJO: '%s'",
        settings.FTS_DAEMON_SLEEP_SIN_TRABAJO)
    logger.info(" + FTS_DAEMON_SLEEP_LIMITE_DE_CANALES: '%s'",
        settings.FTS_DAEMON_SLEEP_LIMITE_DE_CANALES)
    FTS_MAX_LOOPS = int(os.environ.get("FTS_MAX_LOOPS", max_loop))
    FTS_INITIAL_WAIT = float(os.environ.get("FTS_INITIAL_WAIT", initial_wait))
    if FTS_INITIAL_WAIT > 0.0:
        logger.info("Iniciando espera inicial de %s segs...", FTS_INITIAL_WAIT)
        time.sleep(FTS_INITIAL_WAIT)
        logger.info("Espera inicial finalizada")
    Llamador().run(max_loops=FTS_MAX_LOOPS)


if __name__ == '__main__':
    main()
