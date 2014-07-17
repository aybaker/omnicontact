# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.services.depurador_de_campana"""

from __future__ import unicode_literals

from fts_daemon.services.depurador_de_campana import (
    DepuradorDeCampanaWorkflow
, CampanaNoPuedeDepurarseError)
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock


logger = _logging.getLogger(__name__)


class DepuradorDeCampanaWorkflowTests(FTSenderBaseTest):
    """Unit tests de DepuradorDeCampanaWorkflow"""

    def test_llama_a_depurar_con_campana_finalizada(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.estado = Campana.ESTADO_ACTIVA

        depurador = DepuradorDeCampanaWorkflow()
        depurador._obtener_campana = Mock(return_value=campana)
        depurador._depurar = Mock()

        # -----

        depurada_ok = depurador.depurar(1)

        self.assertTrue(depurada_ok)
        depurador._depurar.assert_called_once_with(campana)

    def test_ignora_campana_depurada(self):
        campana = Campana(id=1)
        campana.estado = Campana.ESTADO_DEPURADA

        depurador = DepuradorDeCampanaWorkflow()
        depurador._obtener_campana = Mock(return_value=campana)
        depurador._depurar = Mock()

        # -----

        depurada_ok = depurador.depurar(1)

        self.assertFalse(depurada_ok)
        self.assertEquals(depurador._depurar.call_count, 0)

    def test_reporta_estado_erroneo(self):
        campana = Campana(id=1)
        campana.estado = Campana.ESTADO_PAUSADA

        depurador = DepuradorDeCampanaWorkflow()
        depurador._obtener_campana = Mock(return_value=campana)
        depurador._depurar = Mock(side_effect=depurador._depurar)

        # -----

        with self.assertRaises(CampanaNoPuedeDepurarseError):
            depurador.depurar(1)

        depurador._depurar.assert_called_once_with(campana)

    def test_obtener_campana(self):
        campana_id = self.crear_campana().id
        depurador = DepuradorDeCampanaWorkflow()
        campana = depurador._obtener_campana(campana_id)
        self.assertEquals(campana_id, campana.id)
