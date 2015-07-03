# -*- coding: utf-8 -*-

"""Unittests del servicio prioridad_campana"""

from __future__ import unicode_literals

from fts_web.services.prioridad_evento import PrioridadEventoNoAtendidosService
from fts_web.tests.utiles import FTSenderBaseTest
from fts_daemon.models import EventoDeContacto


class PrioridadEventoNoAtendidos(FTSenderBaseTest):
    """
    Este unit test testa todo los metodos y/o servicios, relacionado con la
   prioriadad de los eventos no atendidos de un contacto
    """

    def test_encuentra_evento_prioridad_no_atendido_busy(self):
        lista_eventos = [1, 2, 11, 21, 32, 33, 35]

        prioridad_evento = PrioridadEventoNoAtendidosService()
        evento_prioridad, indice_evento = prioridad_evento.definir_prioridad_evento(lista_eventos)

        # chequeamos que no devuelva none
        self.assertIsNotNone(evento_prioridad)
        self.assertIsNotNone(indice_evento)

        self.assertEquals(evento_prioridad, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY)

    def test_encuentra_evento_prioridad_no_atendido_no_answer(self):
        lista_eventos = [1, 2, 11, 21, 33, 33, 34, 35]

        prioridad_evento = PrioridadEventoNoAtendidosService()
        evento_prioridad, indice_evento = prioridad_evento.definir_prioridad_evento(lista_eventos)

        # chequeamos que no devuelva none
        self.assertIsNotNone(evento_prioridad)
        self.assertIsNotNone(indice_evento)

        self.assertEquals(evento_prioridad, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER)

    def test_encuentra_evento_prioridad_no_atendido_congestion(self):
        lista_eventos = [1, 2, 11, 21, 36, 36, 35]

        prioridad_evento = PrioridadEventoNoAtendidosService()
        evento_prioridad, indice_evento = prioridad_evento.definir_prioridad_evento(lista_eventos)

        # chequeamos que no devuelva none
        self.assertIsNotNone(evento_prioridad)
        self.assertIsNotNone(indice_evento)

        self.assertEquals(evento_prioridad, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION)

    def test_encuentra_evento_prioridad_no_atendido_canal_no_disponible(self):
        lista_eventos = [1, 2, 11, 21, 35, 34, 36]

        prioridad_evento = PrioridadEventoNoAtendidosService()
        evento_prioridad, indice_evento = prioridad_evento.definir_prioridad_evento(lista_eventos)

        # chequeamos que no devuelva none
        self.assertIsNotNone(evento_prioridad)
        self.assertIsNotNone(indice_evento)

        self.assertEquals(evento_prioridad, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL)

    def test_no_encuentra_evento_prioridad_no_atendido(self):
        lista_eventos = [1, 2, 11, 21, 34, 37]

        prioridad_evento = PrioridadEventoNoAtendidosService()
        evento_prioridad, indice_evento = prioridad_evento.definir_prioridad_evento(lista_eventos)

        # chequeamos que no devuelva none
        self.assertIsNone(evento_prioridad)
        self.assertIsNone(indice_evento)
