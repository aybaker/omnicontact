# -*- coding: utf-8 -*-


from __future__ import unicode_literals

import logging
import re
import json

logger = logging.getLogger(__name__)

from fts_web.errors import FtsError
from fts_web.models import DuracionDeLlamada

from fts_daemon.models import EventoDeContacto


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
        return DuracionDeLlamada.objects.obtener_duracion_de_llamdas(
            numero_telefono)

    def obtener_reporte(self, numero_telefono):
        self._valida_numero_telefono(numero_telefono)

        duracion_de_llamadas = \
            self._obtener_duracion_de_llamadas_de_numero_telefono(
                numero_telefono)

        listado_de_llamadas = []
        for duracion_de_llamada in duracion_de_llamadas:
            listado_de_llamadas.append(ReporteDeTelefonoDTO(
                                       duracion_de_llamada))
        return listado_de_llamadas


class ReporteDeTelefonoDTO(object):
    def __init__(self, duracion_de_llamada):
        self.duracion_de_llamada = duracion_de_llamada
        self.opciones_seleccionadas = self._obtener_opciones_seleccionadas()

    def _obtener_opciones_seleccionadas(self):
        eventos_del_contacto = json.loads(
            self.duracion_de_llamada.eventos_del_contacto)

        opciones_seleccionas = []
        for evento in eventos_del_contacto:
            digito_seleccionado = \
                EventoDeContacto.EVENTO_A_NUMERO_OPCION_MAP[evento]

            opcion_selectionada =\
                self.duracion_de_llamada.campana.opciones.get(
                    digito=digito_seleccionado)

            opciones_seleccionas.append(
                opcion_selectionada.get_descripcion_de_opcion())

        return opciones_seleccionas