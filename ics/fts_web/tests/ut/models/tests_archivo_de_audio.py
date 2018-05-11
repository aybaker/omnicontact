# -*- coding: utf-8 -*-

"""Unittests del modelo Campana"""

from __future__ import unicode_literals

import datetime

from unittest.case import skipIf
from fts_web.models import (ArchivoDeAudio)

from fts_web.tests.utiles import FTSenderBaseTest

from mock import Mock, patch


class EliminarArchivoDeAudioTest(FTSenderBaseTest):

    def test_borrar(self):
        audio = ArchivoDeAudio(id=1)
        audio.save = Mock()

        # -----

        audio.borrar()
        self.assertEqual(audio.borrado, True)

    def test_campana_filtro_de_borradas(self):
        audio = ArchivoDeAudio(id=1)
        audio.save = Mock()

        # -----

        audio.borrar()

        with self.assertRaises(ArchivoDeAudio.DoesNotExist):
            ArchivoDeAudio.objects.get(id=1)
