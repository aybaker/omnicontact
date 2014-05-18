# -*- coding: utf-8 -*-

"""
Middlewares de la aplicacion.
"""

from __future__ import unicode_literals

import logging

logger = logging.getLogger('fts_web')


class ReportErrorMiddleware(object):

    def process_exception(self, request, exception):
        logger.exception("Excepcion detectada")
