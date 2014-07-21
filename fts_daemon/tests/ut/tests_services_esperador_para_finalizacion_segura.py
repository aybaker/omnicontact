# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.services.esperador_para_depuracion_segura"""

from __future__ import unicode_literals

from fts_daemon.services.esperador_para_depuracion_segura import (
    EsperadorParaDepuracionSegura, CantidadMaximaDeIteracionesSuperada
)
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock


logger = _logging.getLogger(__name__)


class EsperadorParaDepuracionSeguraTests(FTSenderBaseTest):
    """Unit tests de EsperadorParaDepuracionSegura"""

    def test_depura_finalizada(self):
        campana = Campana(id=1)
        campana.estado = Campana.ESTADO_FINALIZADA

        depurador = EsperadorParaDepuracionSegura()
        depurador._refrescar_status = Mock(return_value=True)
        depurador.campana_call_status.get_count_llamadas_de_campana = Mock(
            return_value=0)
        depurador._depurar = Mock()
        depurador._sleep = Mock()
        depurador._obtener_campana = Mock(return_value=campana)

        # -----

        depurador.esperar_y_depurar(1)

        depurador._refrescar_status.assert_called_once_with()
        depurador.campana_call_status.get_count_llamadas_de_campana.\
            assert_called_once_with(campana)
        depurador._depurar.assert_called_once_with(1)

    def test_no_depura_si_update_de_status_falla(self):
        campana = Campana(id=1)
        campana.estado = Campana.ESTADO_FINALIZADA

        depurador = EsperadorParaDepuracionSegura()
        depurador._refrescar_status = Mock(return_value=False)
        depurador.campana_call_status.get_count_llamadas_de_campana = Mock(
            return_value=0)
        depurador._depurar = Mock()
        depurador._sleep = Mock()
        depurador._obtener_campana = Mock(return_value=campana)
        depurador.max_loop = 5

        # -----

        with self.assertRaises(CantidadMaximaDeIteracionesSuperada):
            depurador.esperar_y_depurar(1)

        self.assertTrue(depurador._refrescar_status.called)
        self.assertTrue(depurador._sleep.called)
        self.assertFalse(depurador.campana_call_status.\
                         get_count_llamadas_de_campana.called)
        self.assertFalse(depurador._depurar.called)

    def test_no_depura_con_llamadas_en_curso(self):
        campana = Campana(id=1)
        campana.estado = Campana.ESTADO_FINALIZADA

        depurador = EsperadorParaDepuracionSegura()
        depurador._refrescar_status = Mock(return_value=True)
        depurador.campana_call_status.get_count_llamadas_de_campana = Mock(
            return_value=1)
        depurador._depurar = Mock()
        depurador._sleep = Mock()
        depurador._obtener_campana = Mock(return_value=campana)
        depurador.max_loop = 5

        # -----

        with self.assertRaises(CantidadMaximaDeIteracionesSuperada):
            depurador.esperar_y_depurar(1)

        self.assertTrue(depurador._refrescar_status.called)
        self.assertTrue(depurador._sleep.called)
        self.assertTrue(depurador.campana_call_status.\
                         get_count_llamadas_de_campana.called)
        self.assertFalse(depurador._depurar.called)

    def test_obtener_campana(self):
        campana_id = self.crear_campana().id
        depurador = EsperadorParaDepuracionSegura()
        campana = depurador._obtener_campana(campana_id)
        self.assertEquals(campana_id, campana.id)
