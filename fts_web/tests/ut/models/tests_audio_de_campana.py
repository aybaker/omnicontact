# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from django.db import IntegrityError
from django.utils.unittest.case import skipIf
from fts_web.models import (AudioDeCampana)

from fts_web.tests.utiles import FTSenderBaseTest

from mock import Mock, patch


class OrdenUniqueTest(FTSenderBaseTest):
    def test_falla_con_ordenes_iguales(self):
        campana = self.crear_campana_activa()


class ObtieneSiguienteOrdenTest(FTSenderBaseTest):
    def test_devuelve_1(self):
        campana = self.crear_campana_activa()

        # -----
        AudioDeCampana.objects.create(campana=campana, orden=1)
        with self.assertRaises(IntegrityError):
            AudioDeCampana.objects.create(campana=campana, orden=1)

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
