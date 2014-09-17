# -*- coding: utf-8 -*-

"""
Servicio de audios de campañas.
"""

from __future__ import unicode_literals

import logging
import json

from django.conf import settings

from fts_web.errors import FtsError
from fts_web.models import Campana


logger = logging.getLogger(__name__)


class NoSePuedeModificarOrdenError(FtsError):
    """Indica que no se puede inferir los metadatos"""
    pass


class OrdenAudiosCampanaService(object):

    def sube_audio_una_posisicion(self, audio_de_campana):
        """
        Este método intercambia el orden del objeto audio_de_campana pasado
        por parámetro con el objeto audio_de_campana con el siguiente orden.
        """

        audio_superior = audio_de_campana.obtener_audio_siguiente()
        if not audio_superior:
            raise(NoSePuedeModificarOrdenError("No se encontro un siguiente "
                                               "audio para cambiar el orden."))

        orden_audio_de_campana = audio_de_campana.orden
        orden_audio_de_campana_superior = audio_superior.orden

        audio_de_campana.orden = 0
        audio_de_campana.save()
        audio_superior.orden = orden_audio_de_campana
        audio_superior.save()

        audio_de_campana.orden = orden_audio_de_campana_superior
        audio_de_campana.save()

    def baja_audio_una_posisicion(self, audio_de_campana):
        """
        Este método intercambia el orden del objeto audio_de_campana pasado
        por parámetro con el objeto audio_de_campana con el anterior orden.
        """

        audio_inferior = audio_de_campana.obtener_audio_anterior()
        if not audio_inferior:
            raise(NoSePuedeModificarOrdenError("No se encontro un audio "
                                               "anterior para cambiar el "
                                               "orden."))

        orden_audio_de_campana = audio_de_campana.orden
        orden_audio_de_campana_inferior = audio_inferior.orden

        audio_de_campana.orden = 0
        audio_de_campana.save()
        audio_inferior.orden = orden_audio_de_campana
        audio_inferior.save()

        audio_de_campana.orden = orden_audio_de_campana_inferior
        audio_de_campana.save()