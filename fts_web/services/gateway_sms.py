# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import connection
from fts_web.models import CampanaSms
from fts_web.utiles import log_timing

class GatewaySmsService(object):

    def crear_sms_en_el_servidor_ics(self, campana_sms):
        return None
