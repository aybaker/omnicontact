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


class BusquedaDeLlamadasService(object):
    """
    Realiza la búsqueda de las llamadas realizadas a un número de teléfono
    pasado por parámetro.
    """

    def _valida_numero_telefono(self, numero_telefono):
        """
        Valida el numero telefónico tenga  entre 5 y 20 dígitos.
        """
        # TODO: Este método ya se utiliza en el parser. Hay que sacarlo a
        # utiles para no repetir código.

        #numero_telefono = re.sub("[^0-9]", "", str(numero_telefono))
        if not re.match("^[0-9]{5,20}$", numero_telefono):
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

    def buscar_llamadas(self, numero_telefono):
        """
        Método publico del servicio llamado para realizar la búsqueda de las
        llamadas realizadas por un número de teléfono.
        """

        self._valida_numero_telefono(numero_telefono)

        duracion_de_llamadas = \
            self._obtener_duracion_de_llamadas_de_numero_telefono(
                numero_telefono)

        listado_de_llamadas = []
        for duracion_de_llamada in duracion_de_llamadas:
            listado_de_llamadas.append(DetalleDeLlamadaDTO(
                                       duracion_de_llamada))

        return listado_de_llamadas


class OpcionFalsaParaRepresentarAtencionDeLlamada(object):
    """Implementa la api de models.Opcion, para representar que
    la persona atendio la llamada.

    Esto es un workaround. La solucion final deberia eliminar
    esta clase.
    """
    def get_descripcion_de_opcion(self):
        return "Llamada atendida"


ATENCION_DE_LLAMADA_SINGLETON = OpcionFalsaParaRepresentarAtencionDeLlamada()


class DetalleDeLlamadaDTO(object):
    """
    Representa los datos para cada instancia de DuracionDeLlamada de una
    campana.
    """

    def __init__(self, duracion_de_llamada):
        self.duracion_de_llamada = duracion_de_llamada
        self.opciones_seleccionadas = self._obtener_opciones_seleccionadas()

    def _obtener_eventos_del_contacto(self):
        """
        La función de postgres array_agg, a diferencia de json_agg, devuele
        un formato "{val1, val2, val3, ...}"  el cúal no es compatible con
        json.loads(). Por lo que  en este método se obtiene los evento del
        contacto que surgieron de la función de agregación de postgres
        (array_agg) y se modifica para que sea un string válido para json.

        Devuelve listas con NUMERO de evento de contacto,
        por ejemplo: [51, 59] si la persona presiono el digito 1
        y el dígito 9.
        """
        json_string_valido = self.duracion_de_llamada.eventos_del_contacto.replace(
            "{", "[").replace("}", "]")
        return json.loads(json_string_valido)

    def _obtener_opciones_seleccionadas(self):
        """
        Para cada evento de contacto de las instancias DuracionDeLlamada
        obtiene el objeto opción que corresponde en cada caso y las almacena
        en una lista que setea en el atributo opciones_seleccionadas.
        """
        opciones_seleccionas = []
        for evento in self._obtener_eventos_del_contacto():
            digito_seleccionado = \
                EventoDeContacto.EVENTO_A_NUMERO_OPCION_MAP.get(evento, None)

            if digito_seleccionado is None:
                # No es una opción seleccionada, se debe tratar de la llamada atendida
                opciones_seleccionas.append(ATENCION_DE_LLAMADA_SINGLETON)
            else:
                opcion_selectionada = self.duracion_de_llamada.campana.opciones.get(
                    digito=digito_seleccionado)
                opciones_seleccionas.append(opcion_selectionada)

        return opciones_seleccionas
