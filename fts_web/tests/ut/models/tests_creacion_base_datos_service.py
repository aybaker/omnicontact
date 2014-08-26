# -*- coding: utf-8 -*-

"""Unittests del servicio base_de_datos_contacto"""

from __future__ import unicode_literals

import json

from django.core.files import File

from mock import Mock

from fts_web.errors import FtsArchivoImportacionInvalidoError
from fts_web.models import BaseDatosContacto
from fts_web.services.base_de_datos_contactos import CreacionBaseDatosService
from fts_web.tests.utiles import FTSenderBaseTest


class TestGeneraBaseDatosContacto(FTSenderBaseTest):
    def test_genera_base_datos_falla_archivo_xls(self):
        bd = BaseDatosContacto(id=1)
        bd.nombre_archivo_importacion = "planilla-ejemplo-0.xls"
        bd.save = Mock()

        # -----
        creacion_base_de_datos_service = CreacionBaseDatosService()
        with self.assertRaises(FtsArchivoImportacionInvalidoError):
            creacion_base_de_datos_service.genera_base_dato_contacto(bd)

    def test_genera_base_datos_archivo_valido(self):
        bd = BaseDatosContacto(id=1)
        bd.nombre_archivo_importacion = "planilla-ejemplo-0.csv"
        bd.save = Mock()

        # -----

        creacion_base_de_datos_service = CreacionBaseDatosService()
        creacion_base_de_datos_service.genera_base_dato_contacto(bd)

    def test_guarda_metadata(self):
        bd = BaseDatosContacto(id=1)
        bd.save = Mock()

        # -----

        creacion_base_de_datos_service = CreacionBaseDatosService()
        creacion_base_de_datos_service.guarda_metadata(
            bd, {'columna_con_telefono': 1})

        metadata = bd.get_metadata()

        self.assertEqual(metadata.columna_con_telefono, 1)

    def test_importa_contacto(self):
        # 3543009865,lkasdjlfkaf,0351156219387
        # 111534509230,dkasjflkja,0351156982639
        # 2830173491,alsdkjfieasdf,3516983419
        # 3560127341,kahvuahdsfasdfa,2954638961

        bd = BaseDatosContacto(id=1)
        bd.archivo_importacion = File(open(self.get_test_resource(
            "planilla-ejemplo-1.csv"), 'r'))
        bd.nombre_archivo_importacion = "planilla-ejemplo-1.csv"
        bd.metadata = json.dumps({'col_telefono': 0})
        bd.save = Mock()

        # -----

        creacion_base_de_datos_service = CreacionBaseDatosService()
        creacion_base_de_datos_service.importa_contactos(bd)

        self.assertEqual(bd.contactos.count(), 4)

    def test_define_base_dato_contacto(self):
        bd = BaseDatosContacto(id=1)
        bd.save = Mock()

        # -----

        creacion_base_de_datos_service = CreacionBaseDatosService()
        creacion_base_de_datos_service.define_base_dato_contacto(bd)

        self.assertEqual(bd.estado, BaseDatosContacto.ESTADO_DEFINIDA)