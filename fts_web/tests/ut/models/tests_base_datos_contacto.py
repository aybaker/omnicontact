# -*- coding: utf-8 -*-

"""Unittests del modelo Campana"""

from __future__ import unicode_literals

import json

from fts_web.models import BaseDatosContacto
from fts_web.tests.utiles import FTSenderBaseTest


class TestMetadataBaseDatosContacto(FTSenderBaseTest):
    """Clase para testear MetadataBaseDatosContacto"""

    def setUp(self):
        self.metadata = {'col_telefono': 6,
                         'cant_col': 9}
        self.metadata_codificada = json.dumps(self.metadata)

    def test_parsea_datos_correctos(self):
        bd = BaseDatosContacto(pk=1, metadata=self.metadata_codificada)

        self.assertEqual(bd.get_metadata().columna_con_telefono, 6)
        self.assertEqual(bd.get_metadata().cantidad_de_columnas, 9)

    def test_guarda_datos_correctos(self):
        bd = BaseDatosContacto(pk=1)
        metadata = bd.get_metadata()
        metadata.cantidad_de_columnas = 4
        metadata.columna_con_telefono = 3

        self.assertDictEqual(json.loads(bd.metadata), {'col_telefono': 3,
                                                       'cant_col': 4})

    def test_valida_columna_con_telefono(self):
        bd = BaseDatosContacto(pk=1)
        metadata = bd.get_metadata()
        metadata.cantidad_de_columnas = 4
        with self.assertRaises(AssertionError):
            # columna_con_telefono NO puede ser 4
            metadata.columna_con_telefono = 4

    def test_valida_nombres_de_columnas(self):
        bd = BaseDatosContacto(pk=1)
        metadata = bd.get_metadata()
        metadata.cantidad_de_columnas = 4
        metadata.nombres_de_columnas = ["a", "b", "c", "d"]
        with self.assertRaises(AssertionError):
            metadata.nombres_de_columnas = ["a", "b", "c"]
        with self.assertRaises(AssertionError):
            metadata.nombres_de_columnas = ["a", "b", "c", "d", "e"]

    def test_genera_valueerror_sin_datos(self):
        with self.assertRaises(ValueError):
            BaseDatosContacto().get_metadata().columna_con_telefono
