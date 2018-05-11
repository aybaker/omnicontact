# -*- coding: utf-8 -*-

"""Tests generales"""

from __future__ import unicode_literals

import os
import tempfile

from django.conf import settings
from fts_daemon.audio_conversor import convertir_audio, \
    convertir_audio_de_campana
from fts_web.errors import FtsAudioConversionError
from fts_web.models import Campana, AudioDeCampana
from fts_web.tests.utiles import FTSenderBaseTest
from fts_web.utiles import crear_archivo_en_media_root


class AsteriskAudioTest(FTSenderBaseTest):

    def setUp(self):
        # output
        self.out_dirname, self.out_filename = crear_archivo_en_media_root(
            "tmp", "converido-", "wav")
        self.abs_output_filename = os.path.join(settings.MEDIA_ROOT,
            self.out_dirname, self.out_filename)

        self.assertTrue(os.path.exists(self.abs_output_filename))
        self.assertTrue(os.path.getsize(self.abs_output_filename) == 0)

    def tearDown(self):
        os.unlink(self.abs_output_filename)

    def test_convertir_audio_valido(self):

        # input
        abs_input_file = self.get_test_resource("wavs/8k16bitpcm.wav")
        self.assertTrue(os.path.exists(abs_input_file))
        self.assertTrue(os.path.getsize(abs_input_file) > 0)

        convertir_audio(abs_input_file, self.abs_output_filename)
        self.assertTrue(os.path.getsize(self.abs_output_filename) > 0)

    def test_convertir_audio_wav_vacio(self):

        # input
        abs_input_file = self.get_test_resource("wavs/empty.wav")

        with self.assertRaises(FtsAudioConversionError):
            convertir_audio(abs_input_file, self.abs_output_filename)

        self.assertTrue(os.path.getsize(self.abs_output_filename) == 0)

#        wav_file = self.get_test_resource("wavs/non-existing.wav")
#        status = convertir_audio(wav_file, AsteriskAudioTest.OUTPUT)
#        self.assertEqual(status, 0)

    def _test_convertir_audio_desde_modelo(self, testfile):
        tmp = None
        campana = None
        self.assertTrue(os.path.exists(settings.MEDIA_ROOT),
            "El directorio configurado en settings.MEDIA_ROOT "
                "NO EXISTE: {0}".format(settings.MEDIA_ROOT))
        try:
            fd, tmp = tempfile.mkstemp(dir=settings.MEDIA_ROOT)
            # Preparamos datos
            tmp_file_obj = os.fdopen(fd, 'w')
            tmp_file_obj.write(
                open(self.get_test_resource(testfile), 'r').read()
            )
            tmp_file_obj.flush()

            campana = self.crear_campana_sin_audio()
            adc = AudioDeCampana.objects.create(
                orden=1,
                audio_original=tmp,
                campana=campana)

            convertir_audio_de_campana(adc)
        finally:
            try:
                os.remove(tmp)
            except:
                pass

            try:
                print str(adc.audio_asterisk)
                # os.remove()
            except:
                pass

    def test_convertir_audio_desde_modelo(self):
        self._test_convertir_audio_desde_modelo("wavs/8k16bitpcm.wav")

        with self.assertRaises(FtsAudioConversionError):
            self._test_convertir_audio_desde_modelo("wavs/empty.wav")
