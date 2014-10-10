# -*- coding: utf-8 -*-


from __future__ import unicode_literals

import logging
import re

logger = logging.getLogger(__name__)

from fts_web.errors import FtsError
from fts_web.models import DuracionDeLlamada


class NumeroDeTelefonoInvalidoError(FtsError):
    pass


class ReporteDeTelefonoService(object):

    def _valida_numero_telefono(self, numero_telefono):
        """
        Valida el numero telefónico tenga  entre 10 y 13 dígitos.
        """
        # TODO: Este método ya se utiliza en el parser. Hay que sacarlo a
        # utiles para no repetir código.

        numero_telefono = re.sub("[^0-9]", "", str(numero_telefono))
        if not re.match("^[0-9]{10,13}$", numero_telefono):
            raise(NumeroDeTelefonoInvalidoError())

    def _obtener_duracion_de_llamadas_de_numero_telefono(self,
                                                         numero_telefono):
        """
        Obtiene los objetos DuracionDeLlamada para el número de teléfono
        pasado por paramentro. Devuelve una lista de objetos o None si no
        encuentra nada.
        """
        return DuracionDeLlamada.objects.filter(
            numero_telefono=numero_telefono)

    def obtener_reporte(self, numero_telefono):
        self._valida_numero_telefono(numero_telefono)

        reporte_telefono = \
            self._obtener_duracion_de_llamadas_de_numero_telefono(
                numero_telefono)

        return reporte_telefono
