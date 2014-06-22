# -*- coding: utf-8 -*-
"""
Exports the statistics to be used by other systems.
"""

from __future__ import unicode_literals

import datetime
import pprint

from django.core.cache import cache
from django.utils import timezone
import logging as _logging


logger = _logging.getLogger(__name__)

STATISTICS_TIMEOUT = 20

STATISTICS_SUGESTED_REFRESH_INTERVAL = 1

STATISTICS_KEY = 'fts-daemon-stats'


class StatisticsService(object):
    """Servicio encargado de administrar las estadisticas
    recibidas por los distintos componentes del Daemon.

    Actualmente, las estadisticas recibidas son expuestas
    usando el cache de Django.
    """

    def __init__(self):
        """Constructor"""

        self._ultimo_update = timezone.now() - datetime.timedelta(days=30)
        """Ultima vez q' se publicaron las estadisticas"""

        self._sugested_refresh_interval_timedelta = datetime.timedelta(
            seconds=STATISTICS_SUGESTED_REFRESH_INTERVAL)

    def publish_statistics(self, stats):
        """Publica las estadisticas al cache. `stats` debe ser un
        diccionario."""
        assert isinstance(stats, dict)

        self._ultimo_update = timezone.now()
        logger.debug("StatisticsService.publish_statistics(): %s", stats)
        cache.set(STATISTICS_KEY, stats, STATISTICS_TIMEOUT)

        # FIXME: quitar este logger.info()
        logger.info("publish_statistics(): se publico: %s",
            pprint.pformat(stats))

    def get_statistics(self):
        """Devuelve diccionario con estadisticas publicadas, o un diccionario
        vacio si no se encontraron estadisticas.
        """
        stats = cache.get(STATISTICS_KEY)
        if stats is None:
            logger.info("StatisticsService.get_statistics(): no se encontraron"
                " estadisticas publicadas.")
            return {}

        # FIXME: quitar este logger.info()
        logger.info("get_statistics(): se encontraron: %s",
            pprint.pformat(stats))
        return stats

    def shoud_update(self):
        """Devuelve booleano indicando si se deberia o no actualizar
        las estadisticas"""
        # ¿Hasta cuando sugerimos que pueden tomarse como validas
        # las estadisticas?
        stats_validas_sugerido_hasta = self._ultimo_update + \
            self._sugested_refresh_interval_timedelta
        if timezone.now() > stats_validas_sugerido_hasta:
            # Ya hace rato no se actualizan. Sugerimos actualizarlas
            return True
        else:
            # No tiene sentido actualizar
            return False
