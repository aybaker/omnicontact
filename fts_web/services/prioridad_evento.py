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

    def definir_prioridad_evento(self, lista_eventos):
        """
        Prioridad de eventos no atendidos en este orden Busy, No answer,
        Failed(chanunavail, congestion)
        :param lista_eventos: Lista con todos los eventos del contacto 
        """
        evento_prioridad = None
        indice_evento = None
        for ev in lista_eventos:
            if ev is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY:
                evento_prioridad = ev
                indice_evento = lista_eventos.index(ev)
                break
            elif ev is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER:
                evento_prioridad = ev
                indice_evento = lista_eventos.index(ev)
            elif ev is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL or\
            ev is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION:
                if not evento_prioridad is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER:
                    evento_prioridad = ev
                    indice_evento = lista_eventos.index(ev)

        return evento_prioridad, indice_evento
