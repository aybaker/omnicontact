# -*- coding: utf-8 -*-

"""Unittests del modelo Campana"""

from __future__ import unicode_literals

import json

from fts_web.models import BaseDatosContacto, MetadataBaseDatosContactoDTO
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
        metadata.cantidad_de_columnas = 2
        metadata.columna_con_telefono = 1
        metadata.nombres_de_columnas = ["A", "B"]
        metadata.primer_fila_es_encabezado = True
        metadata.save()

        self.assertDictEqual(json.loads(bd.metadata),
                             {'col_telefono': 1,
                              'cant_col': 2,
                              'nombres_de_columnas': ["A", "B"],
                              'prim_fila_enc': True,
                              })

    def test_valida_columna_con_telefono(self):
        bd = BaseDatosContacto(pk=1)
        metadata = bd.get_metadata()
        metadata.cantidad_de_columnas = 4
        # metadata.save()

        with self.assertRaises(AssertionError):
            # columna_con_telefono NO puede ser 4
            metadata.columna_con_telefono = 4

    def test_valida_nombres_de_columnas(self):
        bd = BaseDatosContacto(pk=1)
        metadata = bd.get_metadata()
        metadata.cantidad_de_columnas = 4
        metadata.nombres_de_columnas = ["a", "b", "c", "d"]
        # metadata.save()

        with self.assertRaises(AssertionError):
            metadata.nombres_de_columnas = ["a", "b", "c"]
        with self.assertRaises(AssertionError):
            metadata.nombres_de_columnas = ["a", "b", "c", "d", "e"]

    def test_genera_valueerror_sin_datos(self):
        with self.assertRaises(ValueError):
            BaseDatosContacto().get_metadata().columna_con_telefono


class TestMetadataBaseDatosContactoDTO(FTSenderBaseTest):

    def setUp(self):
        metadata = MetadataBaseDatosContactoDTO()
        metadata.cantidad_de_columnas = 5
        metadata.columna_con_telefono = 2
        metadata.columnas_con_fecha = [0, 4]
        metadata.columnas_con_hora = [1]
        metadata.nombres_de_columnas = ["F_ALTA",
                                        "HORA",
                                        "TELEFONO",
                                        "CUIT",
                                        "F_BAJA"
                                        ]
        metadata.primer_fila_es_encabezado = False
        self.metadata = metadata

    def test_valida_metadatos_correcto(self):
        self.metadata.validar_metadatos()

    def test_detecta_col_telefono_incorrecto(self):
        self.metadata._metadata['col_telefono'] = 99
        with self.assertRaises(AssertionError):
            self.metadata.validar_metadatos()

    def test_detecta_cols_fecha_incorrecto(self):
        self.metadata._metadata['cols_fecha'] = [99]
        with self.assertRaises(AssertionError):
            self.metadata.validar_metadatos()

    def test_detecta_cols_hora_incorrecto(self):
        self.metadata._metadata['cols_hora'] = [99]
        with self.assertRaises(AssertionError):
            self.metadata.validar_metadatos()

    def test_detecta_nombres_de_columnas_incorrecto(self):
        # Falta una columna
        self.metadata._metadata['nombres_de_columnas'] = ["F_ALTA",
                                                          "HORA",
                                                          "TELEFONO",
                                                          "CUIT",
                                                          ]
        with self.assertRaises(AssertionError):
            self.metadata.validar_metadatos()

        # Sobra una columna
        self.metadata._metadata['nombres_de_columnas'] = ["F_ALTA",
                                                          "HORA",
                                                          "TELEFONO",
                                                          "CUIT",
                                                          "F_BAJA",
                                                          "EXTRA",
                                                          ]
        with self.assertRaises(AssertionError):
            self.metadata.validar_metadatos()

    def test_detecta_prim_fila_enc_incorrecto(self):
        self.metadata._metadata['prim_fila_enc'] = ''
        with self.assertRaises(AssertionError):
            self.metadata.validar_metadatos()


class TestMetadataBaseDatosContactoParseoDeDatos(FTSenderBaseTest):

    def setUp(self):
        metadata = MetadataBaseDatosContactoDTO()
        metadata.cantidad_de_columnas = 5
        metadata.columna_con_telefono = 2
        metadata.columnas_con_fecha = [0, 4]
        metadata.columnas_con_hora = [1]
        metadata.nombres_de_columnas = ["F_ALTA",
                                        "HORA",
                                        "TELEFONO",
                                        "CUIT",
                                        "F_BAJA"
                                        ]
        metadata.primer_fila_es_encabezado = False
        self.metadata = metadata

        self.datos_json_ok = json.dumps(["xxx",
                                         "xxx",
                                         "01145679999",
                                         "xxx",
                                         "xxx"])

        self.datos_json_con_sobrante = json.dumps(["xxx",
                                                   "xxx",
                                                   "01145679999",
                                                   "xxx",
                                                   "xxx",
                                                   "dato-sobrante",
                                                   ])

        self.datos_json_con_faltantes = json.dumps(["xxx",
                                                    "xxx",
                                                    "01145679999",
                                                    "xxx",
                                                    ])

    def test_obtener_telefono_de_dato_de_contacto(self):
        telefono = self.metadata.obtener_telefono_de_dato_de_contacto(
            self.datos_json_ok)
        self.assertEquals(telefono, "01145679999")

    def test_obtener_telefono__reporta_error_si_sobran_datos(self):
        with self.assertRaises(AssertionError):
            self.metadata.obtener_telefono_de_dato_de_contacto(
                self.datos_json_con_sobrante)

    def test_obtener_telefono__reporta_error_si_faltan_datos(self):
        with self.assertRaises(AssertionError):
            self.metadata.obtener_telefono_de_dato_de_contacto(
                self.datos_json_con_faltantes)

    def test_obtener_telefono_y_datos_extras(self):
        datos_json = json.dumps(["11/11/11",
                                 "11:11:11",
                                 "01145679999",
                                 "00-99555222-1",
                                 "22/22/22"])
        telefono, datos_extra = self.metadata.obtener_telefono_y_datos_extras(
            datos_json)
        self.assertEquals(telefono, "01145679999")
        self.assertDictEqual(datos_extra,
                             {
                              'F_ALTA': '11/11/11',
                              'HORA': '11:11:11',
                              'TELEFONO': '01145679999',
                              'CUIT': '00-99555222-1',
                              'F_BAJA': '22/22/22',
                              })

    def test_obtener_tyde__reporta_error_si_sobran_datos(self):
        with self.assertRaises(AssertionError):
            self.metadata.obtener_telefono_y_datos_extras(
                self.datos_json_con_sobrante)

    def test_obtener_tyde__reporta_error_si_faltan_datos(self):
        with self.assertRaises(AssertionError):
            self.metadata.obtener_telefono_y_datos_extras(
                self.datos_json_con_faltantes)
