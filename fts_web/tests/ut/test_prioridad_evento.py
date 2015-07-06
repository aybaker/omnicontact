# -*- coding: utf-8 -*-

"""Unittests del servicio prioridad_campana"""

from __future__ import unicode_literals

from fts_web.services.DialStatusServicio import DialStatusService
from fts_web.tests.utiles import FTSenderBaseTest
from fts_daemon.models import EventoDeContacto


class PrioridadEventoNoAtendidos(FTSenderBaseTest):
    """
    Este unit test testa todo los metodos y/o servicios, relacionado con la
   prioriadad de los eventos no atendidos de un contacto
    """

    def test_encuentra_dialstatus_prioridad_busy(self):
        lista_eventos = [1, 2, 11, 21, 32, 33, 35]
        lista_tiempo = [' 2015-06-29 14:39:46', ' 2015-06-29 14:39:50',
                        ' 2015-06-29 14:59:46', ' 2015-06-29 14:40:46',
                        ' 2015-06-29 15:00:46', ' 2015-06-29 15:02:46',
                        ' 2015-06-29 15:05:46']

        service_dialstatus = DialStatusService()
        dialstatus_evento_no_atendido = service_dialstatus.\
            definir_prioridad_dialstatus(lista_eventos, lista_tiempo)

        # chequeamos que no devuelva none
        self.assertIsNotNone(dialstatus_evento_no_atendido)

        self.assertEquals(dialstatus_evento_no_atendido.evento, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY)

    def test_encuentra_dialstatus_prioridad_no_answer(self):
        lista_eventos = [1, 2, 11, 21, 33, 33, 34, 35]
        lista_tiempo = [' 2015-06-29 14:39:46', ' 2015-06-29 14:39:50',
                        ' 2015-06-29 14:59:46', ' 2015-06-29 14:40:46',
                        ' 2015-06-29 15:00:46', ' 2015-06-29 15:02:46',
                        ' 2015-06-29 15:05:46', ' 2015-06-29 15:07:46']

        service_dialstatus = DialStatusService()
        dialstatus_evento_no_atendido = service_dialstatus.\
            definir_prioridad_dialstatus(lista_eventos, lista_tiempo)

        # chequeamos que no devuelva none
        self.assertIsNotNone(dialstatus_evento_no_atendido)

        self.assertEquals(dialstatus_evento_no_atendido.evento, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER)

    def test_encuentra_dialstatus_prioridad_congestion(self):
        lista_eventos = [1, 2, 11, 21, 36, 36, 35]
        lista_tiempo = [' 2015-06-29 14:39:46', ' 2015-06-29 14:39:50',
                        ' 2015-06-29 14:59:46', ' 2015-06-29 14:40:46',
                        ' 2015-06-29 15:00:46', ' 2015-06-29 15:02:46',
                        ' 2015-06-29 15:05:46']

        service_dialstatus = DialStatusService()
        dialstatus_evento_no_atendido = service_dialstatus.\
            definir_prioridad_dialstatus(lista_eventos, lista_tiempo)

        # chequeamos que no devuelva none
        self.assertIsNotNone(dialstatus_evento_no_atendido)

        self.assertEquals(dialstatus_evento_no_atendido.evento, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION)

    def test_encuentra_dialstatus_prioridad_canal_no_disponible(self):
        lista_eventos = [1, 2, 11, 21, 35, 34, 36]
        lista_tiempo = [' 2015-06-29 14:39:46', ' 2015-06-29 14:39:50',
                        ' 2015-06-29 14:59:46', ' 2015-06-29 14:40:46',
                        ' 2015-06-29 15:00:46', ' 2015-06-29 15:02:46',
                        ' 2015-06-29 15:05:46']

        service_dialstatus = DialStatusService()
        dialstatus_evento_no_atendido = service_dialstatus.\
            definir_prioridad_dialstatus(lista_eventos, lista_tiempo)

        # chequeamos que no devuelva none
        self.assertIsNotNone(dialstatus_evento_no_atendido)

        self.assertEquals(dialstatus_evento_no_atendido.evento, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL)

    def test_no_encuentra_dialstatus_no_atendido(self):
        lista_eventos = [1, 2, 11, 21, 34, 37]
        lista_tiempo = [' 2015-06-29 14:39:46', ' 2015-06-29 14:39:50',
                        ' 2015-06-29 14:59:46', ' 2015-06-29 14:40:46',
                        ' 2015-06-29 15:00:46', ' 2015-06-29 15:02:46']

        service_dialstatus = DialStatusService()
        dialstatus_evento_no_atendido = service_dialstatus.\
            definir_prioridad_dialstatus(lista_eventos, lista_tiempo)

        # chequeamos que devuelva none
        self.assertIsNone(dialstatus_evento_no_atendido)
