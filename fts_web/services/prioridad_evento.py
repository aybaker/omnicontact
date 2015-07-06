# -*- coding: utf-8 -*-

"""
Servicio define la prioridad de los eventos de las llamadas
"""

from __future__ import unicode_literals
from fts_daemon.models import EventoDeContacto


class PrioridadEventoNoAtendidosService(object):
    """
    Servicio de definicion de eventos no atendidos(busy, no answer,
    chanunavail, congestion )
    """

    def definir_prioridad_evento(self, lista_eventos, lista_tiempo):
        """
        Prioridad de eventos no atendidos en este orden Busy, No answer,
        Failed(chanunavail, congestion)
        :param lista_eventos: Lista con todos los eventos del contacto
        :param lista_tiempo: Lista con todos los tiempos de los eventos 
        """
        dialstatus_evento = None
        dialstatus_timestamp = None
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
                if not dialstatus_evento is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER:
                    dialstatus_evento = un_dialstatus
                    dialstatus_timestamp = un_timestamp

        return dialstatus_evento, dialstatus_timestamp
