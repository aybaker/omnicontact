# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.audio_conversor"""

from __future__ import unicode_literals

import tempfile

from django.conf import settings
from django.test.utils import override_settings
from fts_daemon.audio_conversor import ConversorDeAudioService
from fts_web.models import ArchivoDeAudio
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock
from django.db.models.fields.files import FileField


logger = _logging.getLogger(__name__)


def _tmpdir():
    """Crea directorio temporal"""
    return tempfile.mkdtemp(prefix=".fts-tests-", dir="/dev/shm")


class ConvertirAudioDeArchivoDeAudioGlobalesTests(FTSenderBaseTest):
    """Testea metodo convertir_audio_de_archivo_de_audio_globales() de
    ConversorDeAudioService
    """

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_convierte_audio_primera_vez_funciona(self):
        servicio = ConversorDeAudioService()
        servicio._convertir_audio = Mock()

        original = self.copy_test_resource_to_mediaroot("wavs/8k16bitpcm.wav")

        archivo_de_audio = ArchivoDeAudio(id=1,
                                          descripcion="Audio",
                                          audio_original=original)
        archivo_de_audio.save = Mock()

        # -----

        self.assertFalse(archivo_de_audio.audio_asterisk)
        servicio.convertir_audio_de_archivo_de_audio_globales(
            archivo_de_audio)

        self.assertTrue(archivo_de_audio.audio_asterisk)
        self.assertEqual(servicio._convertir_audio.call_count, 1)
        self.assertEqual(archivo_de_audio.save.call_count, 1)

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_convierte_audio_dos_veces_funciona(self):
        servicio = ConversorDeAudioService()
        servicio._convertir_audio = Mock()

        original1 = self.copy_test_resource_to_mediaroot("wavs/8k16bitpcm.wav")
        original2 = self.copy_test_resource_to_mediaroot("wavs/empty.wav")

        archivo_de_audio = ArchivoDeAudio(id=1,
                                          descripcion="Audio",
                                          audio_original=original1)
        archivo_de_audio.save = Mock()

        self.assertFalse(archivo_de_audio.audio_asterisk)
        servicio.convertir_audio_de_archivo_de_audio_globales(
            archivo_de_audio)

        self.assertTrue(archivo_de_audio.audio_asterisk)
        self.assertEqual(servicio._convertir_audio.call_count, 1)
        self.assertEqual(archivo_de_audio.save.call_count, 1)

        audio_asterisk_frist_call = archivo_de_audio.audio_asterisk

        # -----

        # Convertimos por 2da vez
        archivo_de_audio.audio_original = original2

        servicio.convertir_audio_de_archivo_de_audio_globales(
            archivo_de_audio)

        self.assertTrue(archivo_de_audio.audio_asterisk)
        self.assertEqual(servicio._convertir_audio.call_count, 2)
        self.assertEqual(archivo_de_audio.save.call_count, 2)

        audio_asterisk_second_call = archivo_de_audio.audio_asterisk

        self.assertEqual(audio_asterisk_frist_call,
                         audio_asterisk_second_call,
                         "La 2da ejecucion sobre la misma instancia de "
                         "ArchivoDeAudio ha generado un nombre distinto")

        # Chequeamos que las 2 veces que se convirtio hayan tenido
        # distinto archivo de entreda, pero mismo archivo de salida

        first_call = servicio._convertir_audio.call_args_list[0]
        second_call = servicio._convertir_audio.call_args_list[1]

        fc_p1 = first_call[0][0]
        fc_p2 = first_call[0][1]
        sc_p1 = second_call[0][0]
        sc_p2 = second_call[0][1]

        self.assertNotEqual(fc_p1, sc_p1, "Las 2 veces que se llamo "
                            "convertir_audio_de_archivo_de_audio_globales() "
                            "se ha utilizado el mismo archivo origen, cuando "
                            "debieron ser 2 archivos distintos")
        self.assertEqual(fc_p2, sc_p2, "En diversas llamadas se generaron "
                         "nombres de archivos destinos (convertidos) "
                         "distintos!")


class ObtenerIdArchivoDeAudioDesdePathTests(FTSenderBaseTest):
    """Testea metodo obtener_id_archivo_de_audio_desde_path() de
    ConversorDeAudioService
    """

    def test_devuelve_id_con_path_correcto(self):
        servicio = ConversorDeAudioService()
        path = "audio_asterisk_predefinido/audio-predefinido-123{0}".format(
            settings.TMPL_FTS_AUDIO_CONVERSOR_EXTENSION)

        # -----

        id_archivo = servicio.obtener_id_archivo_de_audio_desde_path(path)
        self.assertEquals(id_archivo, 123)

    def test_devuelve_none_con_path_vacio(self):
        servicio = ConversorDeAudioService()

        path = ""

        # -----

        id_archivo = servicio.obtener_id_archivo_de_audio_desde_path(path)
        self.assertEquals(id_archivo, None)

    def test_devuelve_none_con_filefield_vacio(self):
        servicio = ConversorDeAudioService()

        field = FileField()

        # -----

        with self.assertRaises(TypeError):
            servicio.obtener_id_archivo_de_audio_desde_path(field)

    def test_devuelve_none_con_filename_sin_numeros(self):
        servicio = ConversorDeAudioService()

        # NO TIENE NUMEROS
        path = "audio_asterisk_predefinido/audio-predefinido-{0}".format(
            settings.TMPL_FTS_AUDIO_CONVERSOR_EXTENSION)

        # -----

        id_archivo = servicio.obtener_id_archivo_de_audio_desde_path(path)
        self.assertEquals(id_archivo, None)

    def test_devuelve_none_con_filename_con_letras_no_numeros(self):
        servicio = ConversorDeAudioService()

        # 'abc' en vez de numero
        path = "audio_asterisk_predefinido/audio-predefinido-abc{0}".format(
            settings.TMPL_FTS_AUDIO_CONVERSOR_EXTENSION)

        # -----

        id_archivo = servicio.obtener_id_archivo_de_audio_desde_path(path)
        self.assertEquals(id_archivo, None)

    def test_devuelve_none_con_filename_sin_guion(self):
        servicio = ConversorDeAudioService()

        # FALTA '-'
        path = "audio_asterisk_predefinido/audio-predefinido123{0}".format(
            settings.TMPL_FTS_AUDIO_CONVERSOR_EXTENSION)

        # -----

        id_archivo = servicio.obtener_id_archivo_de_audio_desde_path(path)
        self.assertEquals(id_archivo, None)

    def test_devuelve_none_con_filename_invalido(self):
        servicio = ConversorDeAudioService()

        # NO TIENE NUMEROS
        path = "audio_asterisk_predefinido/jajaja-jojojo-123{0}".format(
            settings.TMPL_FTS_AUDIO_CONVERSOR_EXTENSION)

        # -----

        id_archivo = servicio.obtener_id_archivo_de_audio_desde_path(path)
        self.assertEquals(id_archivo, None)

    def test_devuelve_none_con_dirname_invalido(self):
        servicio = ConversorDeAudioService()
        path = "jajaja/audio-predefinido-123{0}".format(
            settings.TMPL_FTS_AUDIO_CONVERSOR_EXTENSION)

        # -----

        id_archivo = servicio.obtener_id_archivo_de_audio_desde_path(path)
        self.assertEquals(id_archivo, None)
