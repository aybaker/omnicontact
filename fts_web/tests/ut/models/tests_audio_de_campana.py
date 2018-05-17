# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from django.db import IntegrityError
from unittest.case import skipIf
from fts_web.models import (AudioDeCampana)

from fts_web.tests.utiles import FTSenderBaseTest

from mock import Mock, patch


class AudiosDeCampanaMixin():
    def setUp(self):
        AudioDeCampana.objects.all().delete()


class OrdenUniqueTest(AudiosDeCampanaMixin, FTSenderBaseTest):
    def test_falla_con_ordenes_iguales(self):
        campana = self.crear_campana_sin_audio()


class ObtieneSiguienteOrdenTest(AudiosDeCampanaMixin, FTSenderBaseTest):
    def test_devuelve_1(self):
        campana = self.crear_campana_sin_audio()

        # -----

        AudioDeCampana.objects.create(campana=campana, orden=1)
        with self.assertRaises(IntegrityError):
            AudioDeCampana.objects.create(campana=campana, orden=1)

    def test_devuelve_1_a_9(self):
        campana = self.crear_campana_sin_audio()

        for c in range(9):
            orden = AudioDeCampana.objects.obtener_siguiente_orden(campana.pk)
            AudioDeCampana.objects.create(campana=campana, orden=orden)

        # -----

        self.assertEqual(
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
            [ac.orden for ac in AudioDeCampana.objects.filter(
                campana=campana)])


class ObtieneAudioSiguienteTest(AudiosDeCampanaMixin, FTSenderBaseTest):
    def test_devuelve_siguiente(self):
        campana = self.crear_campana_sin_audio()

        for c in range(1, 9):
            AudioDeCampana.objects.create(campana=campana, orden=c)

        adc = AudioDeCampana.objects.all().first()

        # -----

        self.assertEqual(adc.orden, 1)
        self.assertEqual(adc.obtener_audio_siguiente().orden, 2)

    def test_devuelve_none_en_ultimo(self):
        campana = self.crear_campana_sin_audio()

        for c in range(1, 9):
            AudioDeCampana.objects.create(campana=campana, orden=c)

        adc = AudioDeCampana.objects.all().last()

        # -----

        self.assertEqual(adc.orden, 8)
        self.assertEqual(adc.obtener_audio_siguiente(), None)


class ObtieneAudioAnteriorTest(AudiosDeCampanaMixin, FTSenderBaseTest):
    def test_devuelve_siguiente(self):
        campana = self.crear_campana_sin_audio()

        for c in range(1, 9):
            AudioDeCampana.objects.create(campana=campana, orden=c)

        adc = AudioDeCampana.objects.all().last()

        # -----

        self.assertEqual(adc.orden, 8)
        self.assertEqual(adc.obtener_audio_anterior().orden, 7)

    def test_devuelve_none_en_primero(self):
        campana = self.crear_campana_sin_audio()

        for c in range(1, 9):
            AudioDeCampana.objects.create(campana=campana, orden=c)

        adc = AudioDeCampana.objects.all().first()

        # -----

        self.assertEqual(adc.orden, 1)
        self.assertEqual(adc.obtener_audio_anterior(), None)
