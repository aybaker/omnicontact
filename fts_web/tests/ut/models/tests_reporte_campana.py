# -*- coding: utf-8 -*-

"""Unittests del servicio reporte_Campana"""

from __future__ import unicode_literals

import csv
import json
import os
import tempfile

from django.conf import settings
from django.core.files import File
from django.test.utils import override_settings

from mock import Mock

from fts_daemon.models import EventoDeContacto

from fts_web.models import BaseDatosContacto, Campana, Contacto
from fts_web.services.reporte_campana import (ArchivoDeReporteCsv,
                                              ReporteCampanaService)
from fts_web.tests.utiles import FTSenderBaseTest


def _tmpdir():
    """Crea directorio temporal"""

    tmp_dir = tempfile.mkdtemp(prefix=".fts-tests-", dir="/dev/shm")
    os.chmod(tmp_dir, 0777)
    return tmp_dir


def _crea_campana_con_eventos():
    base_dato_contacto = BaseDatosContacto(pk=1)
    base_dato_contacto.save()

    for ic, _ in enumerate(range(10)):
        contacto = Contacto(pk=ic)
        contacto.datos = u'["3513368309", "Carlós", "Ilcobich"]'
        contacto.bd_contacto = base_dato_contacto
        contacto.save()

    campana = Campana(pk=1)
    campana.nombre = "Test"
    campana.cantidad_canales = 1
    campana.cantidad_intentos = 1
    campana.segundos_ring = 1
    campana.bd_contacto = base_dato_contacto
    campana.save()

    for ie, _ in enumerate(range(10)):
        evento_contacto = EventoDeContacto(pk=ie)
        evento_contacto.campana_id = 1
        evento_contacto.contacto_id = ie
        evento_contacto.evento = 1
        evento_contacto.dato = 1
        evento_contacto.save()
    return campana


class TestCreaReporteCsv(FTSenderBaseTest):

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_crea_reporte_csv_no_falla(self):

        campana = _crea_campana_con_eventos()
        campana.estado = Campana.ESTADO_FINALIZADA

        dirname = 'reporte_campana'
        filename = "{0}-reporte.csv".format(campana.id)
        file_path = os.path.join(settings.MEDIA_ROOT, dirname, filename)

        self.assertFalse(os.path.exists(file_path))

        service = ReporteCampanaService()
        service.crea_reporte_csv(campana)

        self.assertTrue(os.path.exists(file_path))

        # Abrimos el archivo y contamos que tenga 10 lineas.
        with open(file_path, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            for c, row in enumerate(reader):
                self.assertTrue(len(row), 11)
        self.assertEqual(c, 10)

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_crea_reporte_csv_falla_campana_activa(self):

        campana = _crea_campana_con_eventos()
        campana.estado = Campana.ESTADO_ACTIVA

        service = ReporteCampanaService()
        with self.assertRaises(AssertionError):
            service.crea_reporte_csv(campana)


class TestObtenerUrlReporte(FTSenderBaseTest):

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_url_reporte_no_falla(self):
        campana = _crea_campana_con_eventos()
        campana.estado = Campana.ESTADO_FINALIZADA

        dirname = 'reporte_campana'
        filename = "{0}-reporte.csv".format(campana.id)
        file_url = "{0}{1}/{2}".format(settings.MEDIA_URL, dirname, filename)

        service = ReporteCampanaService()
        service.crea_reporte_csv(campana)

        campana.estado = Campana.ESTADO_DEPURADA
        self.assertEqual(service.obtener_url_reporte_csv_descargar(campana),
                         file_url)

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_url_reporte_falla_campana_finalizada(self):
        campana = _crea_campana_con_eventos()
        campana.estado = Campana.ESTADO_FINALIZADA

        service = ReporteCampanaService()
        service.crea_reporte_csv(campana)

        with self.assertRaises(AssertionError):
            service.obtener_url_reporte_csv_descargar(campana)

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_obtener_url_reporte_falla_reporte_no_generado(self):
        campana = _crea_campana_con_eventos()
        campana.estado = Campana.ESTADO_FINALIZADA

        service = ReporteCampanaService()

        with self.assertRaises(AssertionError):
            service.obtener_url_reporte_csv_descargar(campana)


class TestArchivoDeReporteCsv(FTSenderBaseTest):

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_crear_archivo_en_directorio_y_ya_existe(self):
        campana = _crea_campana_con_eventos()

        archivo_de_reporte = ArchivoDeReporteCsv(campana)

        # -----

        self.assertFalse(archivo_de_reporte.ya_existe())

        archivo_de_reporte.crear_archivo_en_directorio()
        opciones_por_contacto = [('["3513368309", "Carl\xf3s", "Ilcobich"]',
                                 [1])]
        archivo_de_reporte.escribir_archivo_csv(opciones_por_contacto)

        self.assertTrue(archivo_de_reporte.ya_existe())

    @override_settings(MEDIA_ROOT=_tmpdir())
    def test_escribir_archivo_csv(self):
        campana = _crea_campana_con_eventos()

        archivo_de_reporte = ArchivoDeReporteCsv(campana)
        archivo_de_reporte.crear_archivo_en_directorio()

        opciones_por_contacto = [('["3513368309", "Carl\xf3s", "Ilcobich"]',
                                 [1])]
        archivo_de_reporte.escribir_archivo_csv(opciones_por_contacto)

        # -----

        with open(archivo_de_reporte.ruta, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            for c, row in enumerate(reader):
                self.assertTrue(len(row), 11)
        self.assertEqual(c, 1)
