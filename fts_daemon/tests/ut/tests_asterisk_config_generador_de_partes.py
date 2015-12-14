# -*- coding: utf-8 -*-

"""Tests generales"""

from __future__ import unicode_literals

import datetime

from django.test.utils import override_settings

from fts_daemon.asterisk_config import generar_dialplan, \
    create_dialplan_config_file, generar_queue, create_queue_config_file, \
    reload_config

from fts_daemon.asterisk_config import (
    DialplanConfigCreator, QueueConfigCreator,
    AsteriskConfigReloader, DialplanConfigFile, QueueConfigFile, ConfigFile)

from fts_daemon.asterisk_config_generador_de_partes import *

from fts_web.models import (Opcion, Campana, GrupoAtencion, AudioDeCampana,
                            BaseDatosContacto, ArchivoDeAudio, Calificacion,
                            DerivacionExterna, AgenteGrupoAtencion)
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
        campana = Mock()
        campana.accion_contestador = Campana.ACCION_NINGUNA

        # -----

        generador_para_start = generador.crear_generador_para_start(campana,
                                                                    Mock())
        self.assertTrue(isinstance(generador_para_start, GeneradorParaStart))

    def test_crear_generador_para_start_detectar_contestador(self):
        generador = GeneradorDePedazoDeDialplanFactory()
        campana = Mock()
        campana.accion_contestador = Campana.ACCION_DETECTAR_CONTESTADOR

        # -----

        self.assertTrue(isinstance(generador.crear_generador_para_start(
                                   campana, Mock()),
                                   GeneradorParaStartDetectarContestador))

    def test_crear_generador_para_start_detectar_evitar_contestador(self):
        generador = GeneradorDePedazoDeDialplanFactory()
        campana = Mock()
        campana.accion_contestador = Campana.ACCION_DETECTAR_EVITAR_CONTESTADOR

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_start(
                        campana, Mock()),
                        GeneradorParaStartDetectarYEvitarContestador))

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

    def test_crear_generador_para_audio_con_tts_mensaje(self):
        generador = GeneradorDePedazoDeDialplanFactory()

        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        bd_contacto = BaseDatosContacto(pk=1)
        metadata = bd_contacto.get_metadata()
        metadata.cantidad_de_columnas = 2
        metadata.columna_con_telefono = 0
        metadata.nombres_de_columnas = ["NOMBRE", "FECHA"]
        metadata.primer_fila_es_encabezado = True
        metadata.save()
        campana.bd_contacto = bd_contacto

        audio_de_campana = AudioDeCampana(
            pk=1, orden=1, campana=campana,
            tts_mensaje="Estimado, ${NOMBRE} usted posee una deuda cuyo "
                        "vencimiento con fecha ${FECHA} Para regularizar "
                        "su situación por favor marque 1 y un asesor hablará "
                        "con usted.")

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_audio(
                            audio_de_campana, Mock(), campana),
                        GeneradorParaTtsMensajeSwift))

    @override_settings(FTS_TTS_UTILIZADO='google')
    def test_crear_generador_para_audio_con_tts_de_google(self):
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
                        GeneradorParaTtsUsandoGoogle))

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

    def test_crear_generador_para_hangup(self):
        generador = GeneradorDePedazoDeDialplanFactory()

        # -----

        self.assertTrue(isinstance(generador.crear_generador_para_hangup(
                                   Mock()), GeneradorParaHangup))

    def test_crear_generador_para_opcion_con_opcion_grupo_atencion(self):
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

        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.DERIVAR_GRUPO_ATENCION)
        campana.opciones = [opcion]

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_opcion(opcion, Mock(),
                                                              campana),
                        GeneradorParaOpcionGrupoAtencion))

    def test_crear_generador_para_opcion_con_opcion_derivacion_esterna_dial(self):
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

        derivacion_externa = DerivacionExterna(pk=1, tipo_derivacion=DerivacionExterna.TIPO_DERIVACION_DIAL,
                                               nombre="derivacion_dial",
                                               dial_string="SIP/proveedor/5001"
                                               )

        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.DERIVAR_DERIVACION_EXTERNA,
                        derivacion_externa=derivacion_externa)
        campana.opciones = [opcion]

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_opcion(opcion, Mock(),
                                                              campana),
                        GeneradorParaOpcionDerivacionExternaDial))

    def test_crear_generador_para_opcion_con_opcion_derivacion_esterna_goto(self):
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

        derivacion_externa = DerivacionExterna(pk=1, tipo_derivacion=DerivacionExterna.TIPO_DERIVACION_GOTO,
                                               nombre="derivacion_goto",
                                               dial_string="SIP/proveedor/5001"
                                               )

        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.DERIVAR_DERIVACION_EXTERNA,
                        derivacion_externa=derivacion_externa)
        campana.opciones = [opcion]

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_opcion(opcion, Mock(),
                                                              campana),
                        GeneradorParaOpcionDerivacionExternaGoto))

    def test_crear_generador_para_opcion_con_opcion_repetir(self):
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

        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.REPETIR)
        campana.opciones = [opcion]

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_opcion(opcion, Mock(),
                                                              campana),
                        GeneradorParaOpcionRepetir))

    def test_crear_generador_para_opcion_con_opcion_voicemail(self):
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

        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.VOICEMAIL)
        campana.opciones = [opcion]

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_opcion(opcion, Mock(),
                                                              campana),
                        GeneradorParaOpcionVoicemail))

    def test_crear_generador_para_opcion_con_opcion_calificar(self):
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

        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.CALIFICAR)
        campana.opciones = [opcion]

        # -----

        self.assertTrue(isinstance(
                        generador.crear_generador_para_opcion(opcion, Mock(),
                                                              campana),
                        GeneradorParaOpcionCalificar))

    def test_crear_generador_para_end(self):
        generador = GeneradorDePedazoDeDialplanFactory()

        # -----

        self.assertTrue(isinstance(generador.crear_generador_para_end(
                                   Mock()), GeneradorParaEnd))


class GeneradorParaFailedTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaFailed.generar_pedazo devuelva el
    template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        # -----

        param_failed = {'fts_campana_id': campana.id,
                        'date': str(datetime.datetime.now()),
                        'traceback_lines': "Error"}

        generador = GeneradorParaFailed(param_failed)
        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_FAILED-{0}".format(campana.id))
                        > 0)


class GeneradorParaStartTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaStart.generar_pedazo devuelva el
    template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now())
        }

        generador = GeneradorParaStart(param_generales)
        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_DIALPLAN_START-{0}".format(
            campana.id)))


class GeneradorParaAudioAsteriskTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaAudioAsterisk.generar_pedazo devuelva el
    template correcto.
    """
    @override_settings(FTS_ASTERISK_CONFIG_CHECK_AUDIO_FILE_EXISTS=False)
    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)
        audio_de_campana = AudioDeCampana(
            pk=1, orden=1, campana=campana,
            audio_asterisk='test/audio/for-asterisk.wav')

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now()),
            'fts_audio_de_campana_id': audio_de_campana.id,
            'fts_audio_file': 'audio file',
        }

        generador = GeneradorParaAudioAsterisk(audio_de_campana,
                                               param_generales)

        generador.get_parametros = Mock(return_value=param_generales)

        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_DIALPLAN_PLAY_AUDIO-{0}".format(
            audio_de_campana.id)))


class GeneradorParaArchivoDeAudioTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaArchivoDeAudio.generar_pedazo devuelva el
    template correcto.
    """
    @override_settings(FTS_ASTERISK_CONFIG_CHECK_AUDIO_FILE_EXISTS=False)
    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)
        archivo_de_audio = ArchivoDeAudio(descripcion="ADA")
        audio_de_campana = AudioDeCampana(
            pk=1, orden=1, campana=campana,
            archivo_de_audio=archivo_de_audio)

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now()),
            'fts_audio_de_campana_id': audio_de_campana.id,
            'fts_audio_file': 'audio file',
        }

        generador = GeneradorParaArchivoDeAudio(audio_de_campana,
                                                param_generales)
        generador.get_parametros = Mock(return_value=param_generales)

        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_DIALPLAN_PLAY_AUDIO-{0}".format(
            audio_de_campana.id)))


class GeneradorParaArchivoDeAudioTtsMensaje(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaArchivoDeAudio.generar_pedazo devuelva el
    template correcto.

    Para el caso de tts puro
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)
        audio_de_campana = AudioDeCampana(
            pk=1, orden=1, campana=campana,
            tts_mensaje="Estimado, ${NOMBRE} usted posee una deuda cuyo "
                        "vencimiento con fecha ${FECHA} Para regularizar "
                        "su situación por favor marque 1 y un asesor hablará "
                        "con usted.")

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now()),
            'fts_audio_de_campana_id': audio_de_campana.id,
            'fts_tts_mensaje': audio_de_campana.tts_mensaje,
        }

        generador = GeneradorParaTtsMensajeSwift(audio_de_campana,
                                                 param_generales)
        generador.get_parametros = Mock(return_value=param_generales)

        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_DIALPLAN_TTS_MENSAJE-{0}".format(
            audio_de_campana.id)))


class GeneradorParaTtsHoraTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaTtsHora.generar_pedazo devuelva el
    template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
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

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now())
        }

        generador = GeneradorParaTtsHora(audio_de_campana, param_generales)

        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_DIALPLAN_HORA-{0}".format(
            audio_de_campana.id)))


class GeneradorParaTtsFechaTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaTtsFecha.generar_pedazo devuelva el
    template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
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

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now())
        }

        generador = GeneradorParaTtsFecha(audio_de_campana, param_generales)

        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_DIALPLAN_FECHA-{0}".format(
            audio_de_campana.id)))


class GeneradorParaTtsUsandoGoogleTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaTtsUsandoGoogle.generar_pedazo devuelva
    el template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
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

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now())
        }

        generador = GeneradorParaTtsUsandoGoogle(audio_de_campana,
                                                 param_generales)

        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_DIALPLAN_TTS-{0}".format(
            audio_de_campana.id)))
        self.assertTrue(config.find("googletts") > 0)
        self.assertTrue(config.find("Swift") == -1)


class GeneradorParaTtsUsandoSwiftTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaTtsUsandoSwift.generar_pedazo devuelva
    el template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
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

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now())
        }

        generador = GeneradorParaTtsUsandoSwift(audio_de_campana,
                                                param_generales)

        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_DIALPLAN_TTS-{0}".format(
            audio_de_campana.id)))
        self.assertTrue(config.find("Swift") > 0)
        self.assertTrue(config.find("googletts") == -1)


class GeneradorParaHangupTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaHangup.generar_pedazo devuelva el
    template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now())
        }

        generador = GeneradorParaHangup(param_generales)
        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_DIALPLAN_HANGUP-{0}".format(
            campana.id)))


class GeneradorParaOpcionVoicemailTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaOpcionVoicemail.generar_pedazo devuelva
    el template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.VOICEMAIL)
        campana.opciones = [opcion]

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now()),
            'fts_opcion_id': opcion.id,
            'fts_opcion_digito': opcion.digito,
        }

        generador = GeneradorParaOpcionVoicemail(opcion, param_generales)
        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_OPCION_VOICEMAIL-{0}".format(
            opcion.id)))


class GeneradorParaOpcionCalificarTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaOpcionCalificar.generar_pedazo devuelva
    el template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        calificacion = Calificacion(nombre="TEST", campana=campana)
        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.CALIFICAR, calificacion=calificacion)
        campana.opciones = [opcion]

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now()),
            'fts_opcion_id': opcion.id,
            'fts_opcion_digito': opcion.digito,
        }

        generador = GeneradorParaOpcionCalificar(opcion, param_generales)
        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_OPCION_CALIFICAR-{0}-{1}-{2}\
            ".format(opcion.id, opcion.calificacion.id,
                     opcion.calificacion.nombre)))


class GeneradorParaOpcionGrupoAtencionTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaOpcionGrupoAtencion.generar_pedazo
    devuelva el template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        grupo_atencion = GrupoAtencion(nombre="TEST", timeout=1,
                                       ring_strategy=GrupoAtencion.RINGALL)
        grupo_atencion.save()
        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.DERIVAR_GRUPO_ATENCION,
                        grupo_atencion=grupo_atencion)
        campana.opciones = [opcion]

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now()),
            'fts_opcion_id': opcion.id,
            'fts_opcion_digito': opcion.digito,
        }

        generador = GeneradorParaOpcionGrupoAtencion(opcion, param_generales)
        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_OPCION_DERIVAR_GRUPO_ATENCION-\
            {0}-{1}-{2}".format(opcion.id, opcion.grupo_atencion.id,
                                opcion.grupo_atencion.nombre)))


class GeneradorParaOpcionDerivacionExternaDialTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaOpcionDerivacionExternaDial.generar_pedazo
    devuelva el template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        derivacion_externa = DerivacionExterna(nombre="TEST_DIAL",
                                               dial_string=1,
                                               tipo_derivacion=DerivacionExterna.TIPO_DERIVACION_DIAL)
        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.DERIVAR_DERIVACION_EXTERNA,
                        derivacion_externa=derivacion_externa)
        campana.opciones = [opcion]

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now()),
            'fts_opcion_id': opcion.id,
            'fts_opcion_digito': opcion.digito,
        }

        generador = GeneradorParaOpcionDerivacionExternaDial(opcion,
                                                         param_generales)
        config = generador.generar_pedazo()
        self.assertTrue(config.find(
            "TEMPLATE_OPCION_DERIVAR_DERIVACION_EXTERNA_DIAL-{0}-{1}-{2}".format(
                opcion.id, opcion.derivacion_externa.id,
                opcion.derivacion_externa.nombre)))


class GeneradorParaOpcionDerivacionExternaGotoTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaOpcionDerivacionExternaGoto.generar_pedazo
    devuelva el template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        derivacion_externa = DerivacionExterna(nombre="TEST_GOTO",
                                               dial_string=1,
                                               tipo_derivacion=DerivacionExterna.TIPO_DERIVACION_GOTO)
        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.DERIVAR_DERIVACION_EXTERNA,
                        derivacion_externa=derivacion_externa)
        campana.opciones = [opcion]

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now()),
            'fts_opcion_id': opcion.id,
            'fts_opcion_digito': opcion.digito,
        }

        generador = GeneradorParaOpcionDerivacionExternaGoto(opcion,
                                                         param_generales)
        config = generador.generar_pedazo()
        self.assertTrue(config.find(
            "TEMPLATE_OPCION_DERIVAR_DERIVACION_EXTERNA_GOTO-{0}-{1}-{2}".format(
                opcion.id, opcion.derivacion_externa.id,
                opcion.derivacion_externa.nombre)))


class GeneradorParaOpcionRepetirTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaOpcionRepetir.generar_pedazo
    devuelva el template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        opcion = Opcion(digito=0, campana=campana, accion=Opcion.REPETIR)
        campana.opciones = [opcion]

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now()),
            'fts_opcion_id': opcion.id,
            'fts_opcion_digito': opcion.digito,
        }

        generador = GeneradorParaOpcionRepetir(opcion, param_generales)
        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_OPCION_REPETIR-{0}".format(
                        opcion.id)))


class GeneradorParaEndTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaEnd.generar_pedazo devuelva el
    template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        # -----

        param_generales = {
            'fts_campana_id': campana.id,
            'fts_campana_dial_timeout': campana.segundos_ring,
            'fts_agi_server': '127.0.0.1',
            'fts_dial_url': 'URL TEST',
            'date': str(datetime.datetime.now())
        }

        generador = GeneradorParaEnd(param_generales)
        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_DIALPLAN_END-{0}".format(
            campana.id)))


# ########################################################################### #


class GeneradorDePedazoDeQueueFactoryTest(FTSenderBaseTest):
    """
    Testea que la clase GeneradorDePedazoDeQueueFactory instancie el
    objeto generador adecuado según los parametros proveidos.
    """

    def crear_generador_para_queue(self):
        generador = GeneradorDePedazoDeQueueFactory()

        # -----

        self.assertTrue(isinstance(generador.crear_generador_para_queue(
                                   Mock()), GeneradorParaQueue))

    def crear_generador_para_member(self):
        generador = GeneradorDePedazoDeQueueFactory()

        # -----

        self.assertTrue(isinstance(generador.crear_generador_para_member(
                                   Mock()), GeneradorParaMember))


class GeneradorParaQueueTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaQueue.generar_pedazo devuelva el
    template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        grupo_atencion = GrupoAtencion(nombre="TEST", timeout=1,
                                       ring_strategy=GrupoAtencion.RINGALL)
        grupo_atencion.save()
        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.DERIVAR_GRUPO_ATENCION,
                        grupo_atencion=grupo_atencion)
        campana.opciones = [opcion]

        # -----

        param_generales = {
            'fts_grupo_atencion_id': grupo_atencion.id,
            'fts_grupo_atencion_nombre': grupo_atencion.nombre,
            'fts_queue_name': grupo_atencion.get_nombre_para_asterisk(),
            'fts_strategy': grupo_atencion.get_ring_strategy_para_asterisk(),
            'fts_timeout': grupo_atencion.timeout,
            'date': str(datetime.datetime.now())
        }

        generador = GeneradorParaQueue(param_generales)
        config = generador.generar_pedazo()
        self.assertTrue(config.find("TEMPLATE_QUEUE-{0}".format(
            grupo_atencion.get_nombre_para_asterisk())) > 0)


class GeneradorParaMemberTest(FTSenderBaseTest):
    """
    Testea que el método GeneradorParaMember.generar_pedazo devuelva el
    template correcto.
    """

    def test_generar_pedazo_devuelve_template_correcto(self):
        campana = Campana(pk=1, nombre="C",
                          estado=Campana.ESTADO_ACTIVA,
                          cantidad_canales=1, cantidad_intentos=1,
                          segundos_ring=10)

        grupo_atencion = GrupoAtencion(nombre="TEST", timeout=1,
                                       ring_strategy=GrupoAtencion.RINGALL)
        grupo_atencion.save()
        agente = AgenteGrupoAtencion(numero_interno="1234",
                                     grupo_atencion=grupo_atencion)
        opcion = Opcion(digito=0, campana=campana,
                        accion=Opcion.DERIVAR_GRUPO_ATENCION,
                        grupo_atencion=grupo_atencion)
        campana.opciones = [opcion]

        # -----

        param_generales = {
            'fts_grupo_atencion_id': grupo_atencion.id,
            'fts_grupo_atencion_nombre': grupo_atencion.nombre,
            'fts_queue_name': grupo_atencion.get_nombre_para_asterisk(),
            'fts_strategy': grupo_atencion.get_ring_strategy_para_asterisk(),
            'fts_timeout': grupo_atencion.timeout,
            'date': str(datetime.datetime.now())
        }

        generador = GeneradorParaMember(agente, param_generales)
        config = generador.generar_pedazo()
        self.assertTrue(config.find("agente.id={0}".format(agente.id)) > 0)