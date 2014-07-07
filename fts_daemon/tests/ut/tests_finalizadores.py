# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.finalizador_de_campana.finalizadores"""

from __future__ import unicode_literals

from fts_daemon.finalizador_de_campana.finalizadores import \
    EsperadorParaFinalizacionSegura, FinalizadorDeCampanaWorkflow, \
    CantidadMaximaDeIteracionesSuperada
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock


logger = _logging.getLogger(__name__)


class FinalizadorDeCampanaWorkflowTests(FTSenderBaseTest):
    """Unit tests de FinalizadorDeCampanaWorkflow"""

    def test_finaliza_campana_activa(self):
        campana = Campana(id=1)
        campana.finalizar = Mock()
        campana.procesar_finalizada = Mock()
        campana.estado = Campana.ESTADO_ACTIVA

        obj = FinalizadorDeCampanaWorkflow()
        obj._obtener_campana = Mock(return_value=campana)

        obj.finalizar(1)

        campana.finalizar.assert_called_once_with()
        campana.procesar_finalizada.assert_called_once_with()

    def test_ignora_campana_finalizada(self):
        campana = Campana(id=1)
        campana.finalizar = Mock()
        campana.procesar_finalizada = Mock()
        campana.estado = Campana.ESTADO_FINALIZADA

        obj = FinalizadorDeCampanaWorkflow()
        obj._obtener_campana = Mock(return_value=campana)

        obj.finalizar(1)

        self.assertEquals(campana.finalizar.call_count, 0)
        self.assertEquals(campana.procesar_finalizada.call_count, 0)

    def test_obtener_campana(self):
        campana_id = self.crear_campana().id
        obj = FinalizadorDeCampanaWorkflow()
        campana = obj._obtener_campana(campana_id)
        self.assertEquals(campana_id, campana.id)


class EsperadorParaFinalizacionSeguraTests(FTSenderBaseTest):
    """Unit tests de EsperadorParaFinalizacionSegura"""

    def test_finaliza_pendiente(self):
        campana = Campana(id=1)

        obj = EsperadorParaFinalizacionSegura()
        obj._refrescar_status = Mock(return_value=True)
        obj.campana_call_status.get_count_llamadas_de_campana = Mock(
            return_value=0)
        obj._finalizar = Mock()
        obj._sleep = Mock()
        obj._obtener_campana = Mock(return_value=campana)
        obj.esperar_y_finalizar(1)

        obj._refrescar_status.assert_called_once_with()
        obj.campana_call_status.get_count_llamadas_de_campana.\
            assert_called_once_with(campana)
        obj._finalizar.assert_called_once_with(1)

    def test_no_finaliza_si_update_de_status_falla(self):
        campana = Campana(id=1)

        obj = EsperadorParaFinalizacionSegura()
        obj._refrescar_status = Mock(return_value=False)
        obj.campana_call_status.get_count_llamadas_de_campana = Mock(
            return_value=0)
        obj._finalizar = Mock()
        obj._sleep = Mock()
        obj._obtener_campana = Mock(return_value=campana)
        obj.max_loop = 5

        with self.assertRaises(CantidadMaximaDeIteracionesSuperada):
            obj.esperar_y_finalizar(1)

        self.assertTrue(obj._refrescar_status.called)
        self.assertTrue(obj._sleep.called)
        self.assertFalse(obj.campana_call_status.\
                         get_count_llamadas_de_campana.called)
        self.assertFalse(obj._finalizar.called)

    def test_no_finaliza_con_llamadas_en_curso(self):
        campana = Campana(id=1)

        obj = EsperadorParaFinalizacionSegura()
        obj._refrescar_status = Mock(return_value=True)
        obj.campana_call_status.get_count_llamadas_de_campana = Mock(
            return_value=1)
        obj._finalizar = Mock()
        obj._sleep = Mock()
        obj._obtener_campana = Mock(return_value=campana)
        obj.max_loop = 5

        with self.assertRaises(CantidadMaximaDeIteracionesSuperada):
            obj.esperar_y_finalizar(1)

        self.assertTrue(obj._refrescar_status.called)
        self.assertTrue(obj._sleep.called)
        self.assertTrue(obj.campana_call_status.\
                         get_count_llamadas_de_campana.called)
        self.assertFalse(obj._finalizar.called)

    def test_obtener_campana(self):
        campana_id = self.crear_campana().id
        obj = EsperadorParaFinalizacionSegura()
        campana = obj._obtener_campana(campana_id)
        self.assertEquals(campana_id, campana.id)
