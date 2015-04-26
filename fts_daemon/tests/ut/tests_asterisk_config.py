# -*- coding: utf-8 -*-

"""Tests generales"""

from __future__ import unicode_literals

import re
import tempfile

from django.test.utils import override_settings
from mock import Mock

from fts_daemon.asterisk_config import (
    DialplanConfigCreator, QueueConfigCreator,
    AsteriskConfigReloader, ConfigFile)
from fts_web.models import (Opcion, Campana, GrupoAtencion, AudioDeCampana,
                            BaseDatosContacto, Calificacion)
from fts_web.tests.utiles import FTSenderBaseTest


class ConfigFileMock(object):

    def __init__(self):
        self.contenidos = None

    def write(self, contenidos):
        assert self.contenidos is None
        self.contenidos = contenidos


class CreateDialplanTest(FTSenderBaseTest):
    """
    Estos tests corresponden al método público
    DialplanConfigCreator.create_dialplan().
    """
    def test_create_dialplan_falla_campana_sin_audio(self):
        config_file_mock = ConfigFileMock()

        campanas = []
        for i in range(1, 4):
            campana = Campana(pk=i, nombre="Campaña", estado=Campana.ESTADO_ACTIVA,
                              cantidad_canales=1, cantidad_intentos=1,
                              segundos_ring=10)

            bd_contacto = BaseDatosContacto(pk=i)
            metadata = bd_contacto.get_metadata()
            metadata.cantidad_de_columnas = 1
            metadata.columna_con_telefono = 0
            metadata.nombres_de_columnas = ["TELEFONO"]
            metadata.primer_fila_es_encabezado = True
            metadata.save()
            campana.bd_contacto = bd_contacto

            campanas.append(campana)

        dialplan_config_creator = DialplanConfigCreator()
        dialplan_config_creator._check_audio_file_exist = Mock()
        dialplan_config_creator._obtener_todas_para_generar_dialplan = Mock(
            return_value=campanas)
        dialplan_config_creator._dialplan_config_file = config_file_mock

        # -----

        dialplan_config_creator.create_dialplan()

        self.assertEqual(len(config_file_mock.contenidos), 3)

        config = "\n".join(config_file_mock.contenidos)

        for campana in campanas:
            self.assertTrue(config.find("TEMPLATE_FAILED-{0}".format(
                campana.id)) > 0)

            self.assertTrue(config.find("TEMPLATE_DIALPLAN_START-{0}".format(
                campana.id)) == -1)
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_HANGUP-{0}".format(
                campana.id)) == -1)
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_END-{0}".format(
                campana.id)) == -1)

    def test_create_dialplan_falla_campana_en_definicion(self):
        config_file_mock = ConfigFileMock()

        campanas = []
        for i in range(1, 4):
            campana = Campana(pk=i, nombre="Campaña",
                              estado=Campana.ESTADO_EN_DEFINICION,
                              cantidad_canales=1, cantidad_intentos=1,
                              segundos_ring=10)

            bd_contacto = BaseDatosContacto(pk=i)
            metadata = bd_contacto.get_metadata()
            metadata.cantidad_de_columnas = 1
            metadata.columna_con_telefono = 0
            metadata.nombres_de_columnas = ["TELEFONO"]
            metadata.primer_fila_es_encabezado = True
            metadata.save()
            campana.bd_contacto = bd_contacto

            campanas.append(campana)

        dialplan_config_creator = DialplanConfigCreator()
        dialplan_config_creator._check_audio_file_exist = Mock()
        dialplan_config_creator._obtener_todas_para_generar_dialplan = Mock(
            return_value=campanas)
        dialplan_config_creator._dialplan_config_file = config_file_mock

        # -----

        dialplan_config_creator.create_dialplan()

        self.assertEqual(len(config_file_mock.contenidos), 3)

        config = "\n".join(config_file_mock.contenidos)

        for campana in campanas:
            self.assertTrue(config.find("TEMPLATE_FAILED-{0}".format(
                campana.id)) > 0)

            self.assertTrue(config.find("TEMPLATE_DIALPLAN_START-{0}".format(
                campana.id)) == -1)
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_HANGUP-{0}".format(
                campana.id)) == -1)
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_END-{0}".format(
                campana.id)) == -1)

    def test_create_dialplan_genera_configuracion_campana_finalizada(self):
        config_file_mock = ConfigFileMock()

        campanas = []
        for i in range(1, 4):
            campana = Campana(pk=i, nombre="Campaña",
                              estado=Campana.ESTADO_FINALIZADA,
                              cantidad_canales=1, cantidad_intentos=1,
                              segundos_ring=10)

            bd_contacto = BaseDatosContacto(pk=i)
            metadata = bd_contacto.get_metadata()
            metadata.cantidad_de_columnas = 1
            metadata.columna_con_telefono = 0
            metadata.nombres_de_columnas = ["TELEFONO"]
            metadata.primer_fila_es_encabezado = True
            metadata.save()
            campana.bd_contacto = bd_contacto

            campana.audios_de_campana = [
                AudioDeCampana(pk=i, orden=1, campana=campana,
                               tts="TELEFONO")]

            campanas.append(campana)

        dialplan_config_creator = DialplanConfigCreator()
        dialplan_config_creator._check_audio_file_exist = Mock()
        dialplan_config_creator._obtener_todas_para_generar_dialplan = Mock(
            return_value=campanas)
        dialplan_config_creator._dialplan_config_file = config_file_mock

        # -----

        dialplan_config_creator.create_dialplan()

        self.assertEqual(len(config_file_mock.contenidos), 3)

        config = "\n".join(config_file_mock.contenidos)

        for campana in campanas:
            self.assertTrue(
                config.find("TEMPLATE_DIALPLAN_START-{0}".format(
                    campana.id)) > 0)
            self.assertTrue(
                config.find("TEMPLATE_DIALPLAN_HANGUP-{0}".format(
                    campana.id)) > 0)
            self.assertTrue(
                config.find("TEMPLATE_DIALPLAN_END-{0}".format(
                    campana.id)) > 0)

    def test_create_dialplan_genera_configuracion_sin_campana_mala(self):
        config_file_mock = ConfigFileMock()

        campanas = []
        for i in range(1, 4):
            campana = Campana(pk=i, nombre="Campaña", estado=Campana.ESTADO_ACTIVA,
                              cantidad_canales=1, cantidad_intentos=1,
                              segundos_ring=10)
            if campana.pk == 1:
                campana.segundos_ring = None

            bd_contacto = BaseDatosContacto(pk=i)
            metadata = bd_contacto.get_metadata()
            metadata.cantidad_de_columnas = 1
            metadata.columna_con_telefono = 0
            metadata.nombres_de_columnas = ["TELEFONO"]
            metadata.primer_fila_es_encabezado = True
            metadata.save()
            campana.bd_contacto = bd_contacto

            campana.audios_de_campana = [
                AudioDeCampana(pk=i, orden=1, campana=campana,
                               tts="TELEFONO")]

            campanas.append(campana)

        dialplan_config_creator = DialplanConfigCreator()
        dialplan_config_creator._check_audio_file_exist = Mock()
        dialplan_config_creator._obtener_todas_para_generar_dialplan = Mock(
            return_value=campanas)
        dialplan_config_creator._dialplan_config_file = config_file_mock

        # -----

        dialplan_config_creator.create_dialplan()

        self.assertEqual(len(config_file_mock.contenidos), 3)

        config = "\n".join(config_file_mock.contenidos)

        for campana in campanas:
            if campana.pk == 1:
                self.assertTrue(
                    config.find("TEMPLATE_DIALPLAN_START-{0}".format(
                        campana.id)) == -1)
                self.assertTrue(
                    config.find("TEMPLATE_FAILED-{0}".format(campana.id)) > 0)
            else:
                self.assertTrue(
                    config.find("TEMPLATE_DIALPLAN_START-{0}".format(
                        campana.id)) > 0)
                self.assertTrue(
                    config.find("TEMPLATE_DIALPLAN_HANGUP-{0}".format(
                        campana.id)) > 0)
                self.assertTrue(
                    config.find("TEMPLATE_DIALPLAN_END-{0}".format(
                        campana.id)) > 0)

    def test_create_dialplan_genera_configuracion_con_opciones(self):

        config_file_mock = ConfigFileMock()

        campanas = []
        for i in range(1, 4):
            campana = Campana(pk=i, nombre="Campaña", estado=Campana.ESTADO_ACTIVA,
                              cantidad_canales=1, cantidad_intentos=1,
                              segundos_ring=10)

            bd_contacto = BaseDatosContacto(pk=i)
            metadata = bd_contacto.get_metadata()
            metadata.cantidad_de_columnas = 1
            metadata.columna_con_telefono = 0
            metadata.nombres_de_columnas = ["TELEFONO"]
            metadata.primer_fila_es_encabezado = True
            metadata.save()
            campana.bd_contacto = bd_contacto

            campana.audios_de_campana = [
                AudioDeCampana(pk=i, orden=1, campana=campana,
                               tts="TELEFONO")]

            campana.opciones = [Opcion(digito=0, accion=Opcion.REPETIR,
                                       campana=campana)]

            campanas.append(campana)

        dialplan_config_creator = DialplanConfigCreator()
        dialplan_config_creator._check_audio_file_exist = Mock()
        dialplan_config_creator._obtener_todas_para_generar_dialplan = Mock(
            return_value=campanas)
        dialplan_config_creator._dialplan_config_file = config_file_mock

        # -----

        dialplan_config_creator.create_dialplan()

        self.assertEqual(len(config_file_mock.contenidos), 3)

        config = "\n".join(config_file_mock.contenidos)

        for campana in campanas:
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_START-{0}".format(
                campana.id)) > 0)
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_HANGUP-{0}".format(
                campana.id)) > 0)
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_END-{0}".format(
                campana.id)) > 0)
            for opcion in campana.opciones.all():
                self.assertTrue(config.find("TEMPLATE_OPCION_REPETIR-{0}"
                                            "".format(opcion.id)) > 0)
        self.assertTrue(campana.opciones.count,
                        len(re.findall('TEMPLATE_OPCION_*', config)))

    def test_create_dialplan_genera_configuracion_con_opcion_calificar(self):

        config_file_mock = ConfigFileMock()

        campanas = []
        for i in range(1, 4):
            campana = Campana(pk=i, nombre="Campaña", estado=Campana.ESTADO_ACTIVA,
                              cantidad_canales=1, cantidad_intentos=1,
                              segundos_ring=10)

            bd_contacto = BaseDatosContacto(pk=i)
            metadata = bd_contacto.get_metadata()
            metadata.cantidad_de_columnas = 1
            metadata.columna_con_telefono = 0
            metadata.nombres_de_columnas = ["TELEFONO"]
            metadata.primer_fila_es_encabezado = True
            metadata.save()
            campana.bd_contacto = bd_contacto

            campana.audios_de_campana = [
                AudioDeCampana(pk=i, orden=1, campana=campana,
                               tts="TELEFONO")]

            calificacion = Calificacion(pk=i, nombre="CALIF", campana=campana)
            calificacion.save()

            campana.opciones = [Opcion(
                digito=0, accion=Opcion.CALIFICAR, calificacion=calificacion,
                campana=campana)]

            campanas.append(campana)

        dialplan_config_creator = DialplanConfigCreator()
        dialplan_config_creator._check_audio_file_exist = Mock()
        dialplan_config_creator._obtener_todas_para_generar_dialplan = Mock(
            return_value=campanas)
        dialplan_config_creator._dialplan_config_file = config_file_mock

        # -----

        dialplan_config_creator.create_dialplan()

        self.assertEqual(len(config_file_mock.contenidos), 3)

        config = "\n".join(config_file_mock.contenidos)
        print config
        for campana in campanas:
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_START-{0}".format(
                campana.id)) > 0)
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_HANGUP-{0}".format(
                campana.id)) > 0)
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_END-{0}".format(
                campana.id)) > 0)
            for opcion in campana.opciones.all():
                self.assertTrue(config.find(
                    "TEMPLATE_OPCION_CALIFICAR-{0}-{1}".format(opcion.id,
                                opcion.calificacion.id)) > 0)

    def test_create_dialplan_genera_configuracion_sin_opciones(self):

        config_file_mock = ConfigFileMock()

        campanas = []
        for i in range(1, 4):
            campana = Campana(pk=i, nombre="Campaña", estado=Campana.ESTADO_ACTIVA,
                              cantidad_canales=1, cantidad_intentos=1,
                              segundos_ring=10)

            bd_contacto = BaseDatosContacto(pk=i)
            metadata = bd_contacto.get_metadata()
            metadata.cantidad_de_columnas = 1
            metadata.columna_con_telefono = 0
            metadata.nombres_de_columnas = ["TELEFONO"]
            metadata.primer_fila_es_encabezado = True
            metadata.save()
            campana.bd_contacto = bd_contacto

            campana.audios_de_campana = [
                AudioDeCampana(pk=i, orden=1, campana=campana,
                               tts="TELEFONO")]

            campanas.append(campana)

        dialplan_config_creator = DialplanConfigCreator()
        dialplan_config_creator._check_audio_file_exist = Mock()
        dialplan_config_creator._obtener_todas_para_generar_dialplan = Mock(
            return_value=campanas)
        dialplan_config_creator._dialplan_config_file = config_file_mock

        # -----

        dialplan_config_creator.create_dialplan()

        self.assertEqual(len(config_file_mock.contenidos), 3)

        config = "\n".join(config_file_mock.contenidos)

        for campana in campanas:
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_START-{0}".format(
                campana.id)) > 0)
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_HANGUP-{0}".format(
                campana.id)) > 0)
            self.assertTrue(config.find("TEMPLATE_DIALPLAN_END-{0}".format(
                campana.id)) > 0)
            self.assertTrue(config.find("TEMPLATE_OPCION") == -1)


class CreateQueueTest(FTSenderBaseTest):
    """
    Estos tests corresponden al método
    QueueConfigCreator.create_queue()
    """

    def test_create_queue_genera_configuracion_correcta(self):

        config_file_mock = ConfigFileMock()

        grupos_de_atencion = [GrupoAtencion(id=1,
                                            nombre="GA1Ñ",
                                            timeout=1),
                              GrupoAtencion(id=2,
                                            nombre="GA2Ñ",
                                            timeout=2)
                              ]

        queue_config_creator = QueueConfigCreator()
        queue_config_creator._obtener_ga_generar_config = Mock(
            return_value=grupos_de_atencion)

        queue_config_creator._queue_config_file = config_file_mock

        # -----

        queue_config_creator.create_queue()

        self.assertEqual(len(config_file_mock.contenidos), 2)

        config = "\n".join(config_file_mock.contenidos)

        for ga in grupos_de_atencion:
            self.assertTrue(config.find("TEMPLATE_QUEUE-{0}".format(
                ga.get_nombre_para_asterisk())) > 0)
            for ag in ga.agentes.all():
                self.assertTrue(config.find("agente.id={0}".format(ag.id)) > 0)


class ReloadConfigTest(FTSenderBaseTest):
    """
    Estos tests corresponden al método
    AsteriskConfigReloader.reload_config()
    """

    @override_settings(FTS_RELOAD_CMD=["/bin/true"])
    def test_status_0(self):
        reload_asterisk_config = AsteriskConfigReloader()

        # -----

        status = reload_asterisk_config.reload_config()
        self.assertEqual(status, 0)

    @override_settings(FTS_RELOAD_CMD=["/bin/false"])
    def test_status_1(self):
        reload_asterisk_config = AsteriskConfigReloader()

        # -----

        status = reload_asterisk_config.reload_config()
        self.assertEqual(status, 1)

    @override_settings(FTS_RELOAD_CMD=["ls", "/", "/root/x/x/x"])
    def test_status_2(self):
        reload_asterisk_config = AsteriskConfigReloader()

        # -----

        status = reload_asterisk_config.reload_config()
        self.assertEqual(status, 2)
