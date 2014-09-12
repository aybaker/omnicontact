# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from django.utils.unittest.case import skipIf
from fts_web.models import (AudioDeCampana)

from fts_web.tests.utiles import FTSenderBaseTest

from mock import Mock, patch


class ObtieneSiguienteOrdenTest(FTSenderBaseTest):
    def test_devuelve_1(self):
        campana = self.crear_campana_activa()

        # -----

        self.assertEqual(AudioDeCampana.objects.obtener_siguiente_orden(
                         campana.pk), 1)

    def test_devuelve_1_a_9(self):
        campana = self.crear_campana_activa()

        for c in range(9):
            orden = AudioDeCampana.objects.obtener_siguiente_orden(campana.pk)
            AudioDeCampana.objects.create(campana=campana, orden=orden)

        # -----

        self.assertEqual(
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            [ac.orden for ac in AudioDeCampana.objects.filter(
                campana=campana)])
