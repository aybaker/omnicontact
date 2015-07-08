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

        dialstatus_evento, dialstatus_timestamp = None, None
        for un_dialstatus, un_timestamp in zip(lista_eventos, lista_tiempo):
            if un_dialstatus is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY:
                dialstatus_evento = un_dialstatus
                dialstatus_timestamp = un_timestamp
                break
            elif un_dialstatus is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER:
                dialstatus_evento = un_dialstatus
                dialstatus_timestamp = un_timestamp
            elif un_dialstatus is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL or\
                    un_dialstatus is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION:
                if dialstatus_evento is not EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER:
                    dialstatus_evento = un_dialstatus
                    dialstatus_timestamp = un_timestamp

        if dialstatus_evento is None:
            return None
        else:
            return DatosDialStatus(dialstatus_evento, dialstatus_timestamp,
                                   self._mapear_dialstatu_nombre(dialstatus_evento))

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
