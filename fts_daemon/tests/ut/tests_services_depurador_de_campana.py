# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.finalizador_de_campana.finalizadores"""

from __future__ import unicode_literals

from fts_daemon.services.depurador_de_campana import (
    DepuradorDeCampanaWorkflow
)
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock


logger = _logging.getLogger(__name__)


class DepuradorDeCampanaWorkflowTests(FTSenderBaseTest):
    """Unit tests de DepuradorDeCampanaWorkflow"""

    def test_llama_a_finaliza_con_campana_activa(self):
        campana = Campana(id=1)
        campana.save = Mock()
        campana.estado = Campana.ESTADO_ACTIVA

        finalizador = DepuradorDeCampanaWorkflow()
        finalizador._obtener_campana = Mock(return_value=campana)
        finalizador._finalizar = Mock()

        # -----

        finalizador.finalizar(1)

        finalizador._finalizar.assert_called_once_with(campana)

    def test_ignora_campana_finalizada(self):
        campana = Campana(id=1)
        campana.estado = Campana.ESTADO_FINALIZADA

        finalizador = DepuradorDeCampanaWorkflow()
        finalizador._obtener_campana = Mock(return_value=campana)
        finalizador._finalizar = Mock()

        # -----

        finalizador.finalizar(1)

        self.assertEquals(finalizador._finalizar.call_count, 0)

    def test_obtener_campana(self):
        campana_id = self.crear_campana().id
        finalizador = DepuradorDeCampanaWorkflow()
        campana = finalizador._obtener_campana(campana_id)
        self.assertEquals(campana_id, campana.id)
