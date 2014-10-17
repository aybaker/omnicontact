# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.test.testcases import TestCase
from mock import Mock, create_autospec

from fts_web.tests.utiles import FTSenderBaseTest
from fts_web.models import DuracionDeLlamada
from fts_web.services.busqueda_de_llamadas_de_numero_de_telefono import (
    BusquedaDeLlamadasService, NumeroDeTelefonoInvalidoError)


class BuscarLlamadasDeUnNumeroTelefonicoTest(FTSenderBaseTest):
    """
    Unit Test del método BusquedaDeLlamadasService.buscar_llamadas()
    """

    def setUp(self):
        self.busqueda_de_llamadas_service = BusquedaDeLlamadasService()
        self.busqueda_de_llamadas_service = Mock(
            spec_set=self.busqueda_de_llamadas_service,
            wraps=self.busqueda_de_llamadas_service)

    def test_funciona_con_numero_telefono_valido(self):
        self.busqueda_de_llamadas_service.buscar_llamadas('3513368309')

    def test_falla_con_numero_telefono_invalido(self):
        with self.assertRaises(NumeroDeTelefonoInvalidoError):
            self.busqueda_de_llamadas_service.buscar_llamadas('35133sdfsd')
