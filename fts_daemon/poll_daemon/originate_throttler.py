# -*- coding: utf-8 -*-
"""

"""

from __future__ import unicode_literals

from datetime import datetime

from django.conf import settings
import logging as _logging


logger = _logging.getLogger(__name__)


# TODO: renombrar OriginateThrottler a OriginateThrottler
class OriginateThrottler(object):
    """Keeps the status of ORIGINATEs and the limits of
    allowed ORIGINATEs per seconds
    """

    def __init__(self):
        # self._originate_ok = datetime.now() - timedelta(days=30)
        self._originate_ok = None
        if settings.FTS_DAEMON_ORIGINATES_PER_SECOND > 0.0:
            self._orig_per_sec = settings.FTS_DAEMON_ORIGINATES_PER_SECOND
            self._max_wait = 1.0 / self._orig_per_sec
        else:
            logger.info("OriginateThrottler: limite desactivado")
            self._orig_per_sec = None
            self._max_wait = None

    # TODO: renombrar a "set_originate_succesfull" o "originate_succesfull"
    def set_originate(self, ok):
        """Set that originate was succesfull or not"""
        if ok:
            self._originate_ok = datetime.now()
        else:
            self._originate_ok = None

    def time_to_sleep(self):
        """How many seconds to wait, to not exceed the limit
        `FTS_DAEMON_ORIGINATES_PER_SECOND`
        """
        if self._originate_ok == None or self._orig_per_sec is None:
            # Primera vez q' se usa, o no hay limite configurado
            return 0.0

        # Calculamos timedelta
        td = datetime.now() - self._originate_ok
        if td.days < 0 or td.days > 0:
            # paso algo raro... esperamos `self._max_wait`
            logger.warn("OriginateThrottler.time_to_sleep(): valor sospechoso "
                "de td.days: %s", td.days)
            return self._max_wait

        # td.days == 0, ahora calculamos `delta` en segundos
        delta = float(td.seconds) + float(td.microseconds) / 1000000.0

        # Si el delta es < 0, paso algo raro!
        if delta < 0.0:
            # paso algo raro... esperamos `self._max_wait`
            logger.warn("OriginateThrottler.time_to_sleep(): valor sospechoso "
                "de delta: %s", delta)
            return self._max_wait

        # Si el delta es > a espera maxima, no esperamos mas
        if delta >= self._max_wait:
            return 0.0

        # Calculamos cuanto tiempo hay que esperar
        to_sleep = self._max_wait - delta
        return to_sleep
