# -*- coding: utf-8 -*-

"""Unittests del servicio audios_campana.py"""

from __future__ import unicode_literals

import datetime

from django.utils.unittest.case import skipIf
from fts_web.models import (AudioDeCampana)

from fts_web.tests.utiles import FTSenderBaseTest
from fts_web.services.audios_campana import (OrdenAudiosCampanaService,
                                             NoSePuedeModificarOrdenError)

from mock import Mock, patch


class BajaAudioUnaPosicionTest(FTSenderBaseTest):

    def test_no_falla(self):
        campana = self.crear_campana_activa()

        for c in range(1, 10):
            AudioDeCampana.objects.create(campana=campana, orden=c)

        # -----

        adc = AudioDeCampana.objects.all().last()
        self.assertEqual(adc.orden, 9)

        orden_audios_campana_service = OrdenAudiosCampanaService()
        orden_audios_campana_service.baja_audio_una_posicion(adc)

        adc = AudioDeCampana.objects.get(pk=adc.pk)
        self.assertEqual(adc.orden, 8)

        orden_audios_campana_service.baja_audio_una_posicion(adc)

        adc = AudioDeCampana.objects.get(pk=adc.pk)
        self.assertEqual(adc.orden, 7)

    def test_falla_primera_posicion(self):
        campana = self.crear_campana_activa()

        for c in range(1, 10):
            AudioDeCampana.objects.create(campana=campana, orden=c)

        # -----

        adc = AudioDeCampana.objects.all().first()
        self.assertEqual(adc.orden, 1)

        orden_audios_campana_service = OrdenAudiosCampanaService()
        with self.assertRaises(NoSePuedeModificarOrdenError):
            orden_audios_campana_service.baja_audio_una_posicion(adc)


class SubeAudioUnaPosicionTest(FTSenderBaseTest):

    def test_no_falla(self):
        campana = self.crear_campana_activa()

        for c in range(1, 10):
            AudioDeCampana.objects.create(campana=campana, orden=c)

        # -----

        adc = AudioDeCampana.objects.all().first()
        self.assertEqual(adc.orden, 1)

        orden_audios_campana_service = OrdenAudiosCampanaService()
        orden_audios_campana_service.sube_audio_una_posicion(adc)

        adc = AudioDeCampana.objects.get(pk=adc.pk)
        self.assertEqual(adc.orden, 2)

        orden_audios_campana_service.sube_audio_una_posicion(adc)

        adc = AudioDeCampana.objects.get(pk=adc.pk)
        self.assertEqual(adc.orden, 3)

    def test_falla_ultima_posicion(self):
        campana = self.crear_campana_activa()

        for c in range(1, 10):
            AudioDeCampana.objects.create(campana=campana, orden=c)

        # -----

        adc = AudioDeCampana.objects.all().last()
        self.assertEqual(adc.orden, 9)

        orden_audios_campana_service = OrdenAudiosCampanaService()
        with self.assertRaises(NoSePuedeModificarOrdenError):
            orden_audios_campana_service.sube_audio_una_posicion(adc)