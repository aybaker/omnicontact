# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.finalizador_de_campana.finalizadores"""

from __future__ import unicode_literals

import unittest

from django.utils.unittest.case import skipIf
from fts_daemon.finalizador_de_campana.finalizadores import \
    EsperadorParaDepuracionSegura, DepuradorDeCampanaWorkflow, \
    CantidadMaximaDeIteracionesSuperada
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock


logger = _logging.getLogger(__name__)


class DepuradorDeCampanaWorkflowTests(FTSenderBaseTest):
    """Integration tests de DepuradorDeCampanaWorkflow"""

    def test_finaliza_campana(self):
        campana_id = self.crear_campana_activa().id
        finalizador = DepuradorDeCampanaWorkflow()
        finalizador.finalizar(campana_id)


class EsperadorParaDepuracionSeguraTests(FTSenderBaseTest):
    """Integration tests de EsperadorParaDepuracionSegura"""

    # FIXME: implementar
