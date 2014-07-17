# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.finalizador_de_campana.finalizadores"""

from __future__ import unicode_literals

import unittest

from django.utils.unittest.case import skipIf
from fts_daemon.services.depurador_de_campana import DepuradorDeCampanaWorkflow
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock


logger = _logging.getLogger(__name__)


class DepuradorDeCampanaWorkflowIntegTests(FTSenderBaseTest):
    """Integration tests de DepuradorDeCampanaWorkflow"""

    def test_depura_campana_finalizada(self):
        campana = self.crear_campana_finalizada()
        depurador = DepuradorDeCampanaWorkflow()

        # -----

        depurada = depurador.depurar(campana.id)
        self.assertTrue(depurada)
        self.assertEquals(Campana.objects.get(pk=campana.id).estado,
                          Campana.ESTADO_DEPURADA)


class EsperadorParaDepuracionSeguraIntegTests(FTSenderBaseTest):
    """Integration tests de EsperadorParaDepuracionSegura"""

    # FIXME: implementar
