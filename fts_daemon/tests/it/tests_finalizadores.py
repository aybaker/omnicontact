# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.finalizador_de_campana.finalizadores"""

from __future__ import unicode_literals

import unittest

from django.utils.unittest.case import skipIf
from fts_daemon.finalizador_de_campana.finalizadores import \
    EsperadorParaFinalizacionSegura, FinalizadorDeCampanaWorkflow, \
    CantidadMaximaDeIteracionesSuperada
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock


logger = _logging.getLogger(__name__)


class FinalizadorDeCampanaWorkflowTests(FTSenderBaseTest):
    """Integration tests de FinalizadorDeCampanaWorkflow"""

    def test_finaliza_campana(self):
        campana_id = self.crear_campana_activa().id
        finalizador = FinalizadorDeCampanaWorkflow()
        finalizador.finalizar(campana_id)


class EsperadorParaFinalizacionSeguraTests(FTSenderBaseTest):
    """Integration tests de EsperadorParaFinalizacionSegura"""

    # FIXME: implementar
