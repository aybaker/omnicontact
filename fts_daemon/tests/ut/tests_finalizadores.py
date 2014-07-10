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

    def test_llama_a_finaliza_con_campana_activa(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.estado = Campana.ESTADO_ACTIVA

        finalizador = FinalizadorDeCampanaWorkflow()
        finalizador._obtener_campana = Mock(return_value=campana)
        finalizador._finalizar = Mock()

        # -----

        finalizador.finalizar(1)

        finalizador._finalizar.assert_called_once_with(campana)

    def test_ignora_campana_finalizada(self):
        campana = Campana(id=1)
        campana.estado = Campana.ESTADO_FINALIZADA

        finalizador = FinalizadorDeCampanaWorkflow()
        finalizador._obtener_campana = Mock(return_value=campana)
        finalizador._finalizar = Mock()

        # -----

        finalizador.finalizar(1)

        self.assertEquals(finalizador._finalizar.call_count, 0)

    def test_obtener_campana(self):
        campana_id = self.crear_campana().id
        finalizador = FinalizadorDeCampanaWorkflow()
        campana = finalizador._obtener_campana(campana_id)
        self.assertEquals(campana_id, campana.id)


class EsperadorParaFinalizacionSeguraTests(FTSenderBaseTest):
    """Unit tests de EsperadorParaFinalizacionSegura"""

    def test_finaliza_pendiente(self):
        campana = Campana(id=1)

        finalizador = EsperadorParaFinalizacionSegura()
        finalizador._refrescar_status = Mock(return_value=True)
        finalizador.campana_call_status.get_count_llamadas_de_campana = Mock(
            return_value=0)
        finalizador._finalizar = Mock()
        finalizador._sleep = Mock()
        finalizador._obtener_campana = Mock(return_value=campana)
        finalizador.esperar_y_finalizar(1)

        finalizador._refrescar_status.assert_called_once_with()
        finalizador.campana_call_status.get_count_llamadas_de_campana.\
            assert_called_once_with(campana)
        finalizador._finalizar.assert_called_once_with(1)

    def test_no_finaliza_si_update_de_status_falla(self):
        campana = Campana(id=1)

        finalizador = EsperadorParaFinalizacionSegura()
        finalizador._refrescar_status = Mock(return_value=False)
        finalizador.campana_call_status.get_count_llamadas_de_campana = Mock(
            return_value=0)
        finalizador._finalizar = Mock()
        finalizador._sleep = Mock()
        finalizador._obtener_campana = Mock(return_value=campana)
        finalizador.max_loop = 5

        with self.assertRaises(CantidadMaximaDeIteracionesSuperada):
            finalizador.esperar_y_finalizar(1)

        self.assertTrue(finalizador._refrescar_status.called)
        self.assertTrue(finalizador._sleep.called)
        self.assertFalse(finalizador.campana_call_status.\
                         get_count_llamadas_de_campana.called)
        self.assertFalse(finalizador._finalizar.called)

    def test_no_finaliza_con_llamadas_en_curso(self):
        campana = Campana(id=1)

        finalizador = EsperadorParaFinalizacionSegura()
        finalizador._refrescar_status = Mock(return_value=True)
        finalizador.campana_call_status.get_count_llamadas_de_campana = Mock(
            return_value=1)
        finalizador._finalizar = Mock()
        finalizador._sleep = Mock()
        finalizador._obtener_campana = Mock(return_value=campana)
        finalizador.max_loop = 5

        with self.assertRaises(CantidadMaximaDeIteracionesSuperada):
            finalizador.esperar_y_finalizar(1)

        self.assertTrue(finalizador._refrescar_status.called)
        self.assertTrue(finalizador._sleep.called)
        self.assertTrue(finalizador.campana_call_status.\
                         get_count_llamadas_de_campana.called)
        self.assertFalse(finalizador._finalizar.called)

    def test_obtener_campana(self):
        campana_id = self.crear_campana().id
        finalizador = EsperadorParaFinalizacionSegura()
        campana = finalizador._obtener_campana(campana_id)
        self.assertEquals(campana_id, campana.id)
