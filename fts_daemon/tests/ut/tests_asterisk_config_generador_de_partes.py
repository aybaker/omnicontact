# -*- coding: utf-8 -*-

"""Tests generales"""

from __future__ import unicode_literals

import logging
import tempfile
import re
import os

from django.conf import settings
from django.test.utils import override_settings

from fts_daemon.asterisk_config import generar_dialplan, \
    create_dialplan_config_file, generar_queue, create_queue_config_file, \
    reload_config

from fts_daemon.asterisk_config import (
    NoSePuedeCrearDialplanError, DialplanConfigCreator, QueueConfigCreator,
    AsteriskConfigReloader, DialplanConfigFile, QueueConfigFile, ConfigFile)

from fts_daemon.asterisk_config_generador_de_partes import (
    GeneradorDePedazoDeDialplanFactory, GeneradorParaFailed,
    GeneradorParaStart, GeneradorParaAudioAsterisk,
    GeneradorParaArchivoDeAudio, GeneradorParaTtsHora, GeneradorParaTtsFecha,
    GeneradorParaTts)

from fts_web.models import (Opcion, Campana, GrupoAtencion, AudioDeCampana,
                            BaseDatosContacto, ArchivoDeAudio, Calificacion)
from fts_web.tests.utiles import FTSenderBaseTest

from mock import Mock


class GeneradorDePedazoDeDialplanFactoryTest(FTSenderBaseTest):
    """
    Testea que la clase GeneradorDePedazoDeDialplanFactory instancie el
    objeto generador adecuado según los parametros proveidos.
    """

    def test_crear_generador_para_failed(self):
        generador = GeneradorDePedazoDeDialplanFactory()

        # -----

        self.assertTrue(isinstance(generador.crear_generador_para_failed(
                                   Mock()), GeneradorParaFailed))

    def test_crear_generador_para_start(self):
        generador = GeneradorDePedazoDeDialplanFactory()

        # -----

        self.assertTrue(isinstance(generador.crear_generador_para_start(
                                   Mock()), GeneradorParaStart))

    def test_crear_generador_para_audio_con_audio_asterisk(self):
        generador = GeneradorDePedazoDeDialplanFactory()

        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        bd_contacto = BaseDatosContacto(pk=1)
        metadata = bd_contacto.get_metadata()
        metadata.cantidad_de_columnas = 1
        metadata.columna_con_telefono = 0
        metadata.nombres_de_columnas = ["TELEFONO"]
        metadata.primer_fila_es_encabezado = True
        metadata.save()
        campana.bd_contacto = bd_contacto

        audio_de_campana = AudioDeCampana(
            pk=1, orden=1, campana=campana,
            audio_asterisk='test/audio/for-asterisk.wav')

        campana.audios_de_campana = [audio_de_campana]

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_audio(
                            audio_de_campana, Mock(), campana),
                        GeneradorParaAudioAsterisk))

    def test_crear_generador_para_audio_con_archivo_de_audio(self):
        generador = GeneradorDePedazoDeDialplanFactory()

        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        bd_contacto = BaseDatosContacto(pk=1)
        metadata = bd_contacto.get_metadata()
        metadata.cantidad_de_columnas = 1
        metadata.columna_con_telefono = 0
        metadata.nombres_de_columnas = ["TELEFONO"]
        metadata.primer_fila_es_encabezado = True
        metadata.save()
        campana.bd_contacto = bd_contacto

        archivo_de_audio = ArchivoDeAudio(descripcion="ADA")
        audio_de_campana = AudioDeCampana(
            pk=1, orden=1, campana=campana,
            archivo_de_audio=archivo_de_audio)

        campana.audios_de_campana = [audio_de_campana]

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_audio(
                            audio_de_campana, Mock(), campana),
                        GeneradorParaArchivoDeAudio))

    def test_crear_generador_para_audio_con_tts(self):
        generador = GeneradorDePedazoDeDialplanFactory()

        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        bd_contacto = BaseDatosContacto(pk=1)
        metadata = bd_contacto.get_metadata()
        metadata.cantidad_de_columnas = 1
        metadata.columna_con_telefono = 0
        metadata.nombres_de_columnas = ["TELEFONO"]
        metadata.primer_fila_es_encabezado = True
        metadata.save()
        campana.bd_contacto = bd_contacto

        audio_de_campana = AudioDeCampana(pk=1, orden=1, campana=campana,
                                          tts="TELEFONO")
        campana.audios_de_campana = [audio_de_campana]

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_audio(
                            audio_de_campana, Mock(), campana),
                        GeneradorParaTts))

    def test_crear_generador_para_audio_con_tts_fecha(self):
        generador = GeneradorDePedazoDeDialplanFactory()

        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        bd_contacto = BaseDatosContacto(pk=1)
        metadata = bd_contacto.get_metadata()
        metadata.cantidad_de_columnas = 2
        metadata.columna_con_telefono = 0
        metadata.columnas_con_fecha = [1]
        metadata.nombres_de_columnas = ['TELEFONO', "FECHA"]
        metadata.primer_fila_es_encabezado = True
        metadata.save()
        campana.bd_contacto = bd_contacto

        audio_de_campana = AudioDeCampana(pk=1, orden=1, campana=campana,
                                          tts="FECHA")
        campana.audios_de_campana = [audio_de_campana]

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_audio(
                            audio_de_campana, Mock(), campana),
                        GeneradorParaTtsFecha))

    def test_crear_generador_para_audio_con_tts_hora(self):
        generador = GeneradorDePedazoDeDialplanFactory()

        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        bd_contacto = BaseDatosContacto(pk=1)
        metadata = bd_contacto.get_metadata()
        metadata.cantidad_de_columnas = 2
        metadata.columna_con_telefono = 0
        metadata.columnas_con_hora = [1]
        metadata.nombres_de_columnas = ['TELEFONO', "HORA"]
        metadata.primer_fila_es_encabezado = True
        metadata.save()
        campana.bd_contacto = bd_contacto

        audio_de_campana = AudioDeCampana(pk=1, orden=1, campana=campana,
                                          tts="HORA")
        campana.audios_de_campana = [audio_de_campana]

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_audio(
                            audio_de_campana, Mock(), campana),
                        GeneradorParaTtsHora))
