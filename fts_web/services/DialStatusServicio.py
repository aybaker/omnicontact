# -*- coding: utf-8 -*-

"""
Servicio define la prioridad de los eventos de las llamadas
"""

from __future__ import unicode_literals
from fts_daemon.models import EventoDeContacto


class DialStatusService(object):
    """
    Servicio de dialstatus
    http://www.voip-info.org/wiki/view/Asterisk+variable+DIALSTATUS
    """

    def definir_prioridad_dialstatus(self, lista_eventos, lista_tiempo):
        """
        Define prioridad de dialstatus de los siguientes eventos en ese orden
        Busy, No answer, Failed(chanunavail, congestion)
        :param lista_eventos: Lista con todos los eventos del contacto
        :param lista_tiempo: Lista con todos los tiempos de los eventos
        """

        # Primero, vemos si existe EVENTO_ASTERISK_DIALSTATUS_BUSY
        lista_evento_timestamp = [(evento, timestamp)
                                  for evento, timestamp in zip(lista_eventos, lista_tiempo)
                                  if evento == EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY]

        if lista_evento_timestamp:
            evento, timestamp = lista_evento_timestamp[-1]
            return DatosDialStatus(evento, timestamp, self._mapear_dialstatu_nombre(evento))

        # Segundo, vemos si existe EVENTO_ASTERISK_DIALSTATUS_NOANSWER
        lista_evento_timestamp = [(evento, timestamp)
                                  for evento, timestamp in zip(lista_eventos, lista_tiempo)
                                  if evento == EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER]

        if lista_evento_timestamp:
            evento, timestamp = lista_evento_timestamp[-1]
            return DatosDialStatus(evento, timestamp, self._mapear_dialstatu_nombre(evento))

        # Finalmente, vemos si existe EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL o EVENTO_ASTERISK_DIALSTATUS_CONGESTION
        lista_evento_timestamp = [(evento, timestamp)
                                  for evento, timestamp in zip(lista_eventos, lista_tiempo)
                                  if evento in (EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL,
                                                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION)]

        if lista_evento_timestamp:
            evento, timestamp = lista_evento_timestamp[-1]
            return DatosDialStatus(evento, timestamp, self._mapear_dialstatu_nombre(evento))

        # Si no encontramos ninguno de los eventos que nos interesan, devolvemos None
        return None

    def _mapear_dialstatu_nombre(self, dialstatus_evento):
        if dialstatus_evento is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY:
            return "Ocupado"
        elif dialstatus_evento is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER:
            return "No contesto"
        elif dialstatus_evento is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL:
            return "Canal no disponible"
        elif dialstatus_evento is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION:
            return "Congestion"
        else:
            return None


class DatosDialStatus(object):
    """Encapsula los datos del dialstatus.
    """

    def __init__(self, evento, timestamp, nombre_dialstatus):

        self._evento = evento
        self._timestamp = timestamp
        self._nombre_dialstatus = nombre_dialstatus

    @property
    def evento(self):
        return self._evento

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def nombre_dialstatus(self):
        return self._nombre_dialstatus
