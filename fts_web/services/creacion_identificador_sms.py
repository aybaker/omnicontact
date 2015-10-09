# -*- coding: utf-8 -*-

"""
Servicio define la prioridad de los eventos de las llamadas
"""

from __future__ import unicode_literals
from fts_web.models import CampanaSms


class IndentificadorSmsService(object):
    """
    Servicio de indentificador para campana sms
    """
    def obtener_ultimo_identificador_sms(self):
        """
        Este metodo se encarga de devolver el siguinte identificador sms
        y si no existe campana sms me devuelve 1000
        """
        try:
            identificador = \
                CampanaSms.objects.latest('id').identificador_campana_sms + 1
        except CampanaSms.DoesNotExist:
            identificador = 1000

        return identificador
