# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.test.testcases import TestCase
from mock import Mock, create_autospec

from fts_web.tests.utiles import FTSenderBaseTest
from fts_web.models import DuracionDeLlamada
from fts_web.services.reporte_de_numero_de_telefono import (
    ReporteDeTelefonoService, NumeroDeTelefonoInvalidoError)


class ObtenerReporteDeLlamadasDeUnNumeroTelefonicoTest(FTSenderBaseTest):
    """
    Unit Test del método ReporteDeTelefonoService.obtener_reporte()
    """

    def setUp(self):
        self.reporte_de_telefono_service = ReporteDeTelefonoService()
        self.reporte_de_telefono_service = Mock(
            spec_set=self.reporte_de_telefono_service,
            wraps=self.reporte_de_telefono_service)

    def test_funciona_con_numero_telefono_valido(self):
        self.reporte_de_telefono_service.obtener_reporte('3513368309')

    def test_falla_con_numero_telefono_invalido(self):
        with self.assertRaises(NumeroDeTelefonoInvalidoError):
            self.reporte_de_telefono_service.obtener_reporte('35133sdfsd')

    def test_funciona_con_numero_telefono_valido(self):
        duracion_de_llamada = DuracionDeLlamada(pk=1)

        self.reporte_de_telefono_service.\
            _obtener_duracion_de_llamadas_de_numero_telefono.return_value = [
                duracion_de_llamada]

        # -----

        self.assertEqual(self.reporte_de_telefono_service.obtener_reporte(
            '3513368309'), [duracion_de_llamada])
