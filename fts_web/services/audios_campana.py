# -*- coding: utf-8 -*-

"""
Servicio de audios de campañas.
"""

from __future__ import unicode_literals

import logging
import json

from django.conf import settings
from fts_web.models import Campana


logger = logging.getLogger(__name__)


class OrdenAudiosCampanaService(object):

    def ordenar_audios_campana(self, audio_de_campana, direccion):
        pass