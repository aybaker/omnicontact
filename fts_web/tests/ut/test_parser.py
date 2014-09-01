# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from django.test.utils import override_settings


from fts_web.parser import ParserCsv, validate_number, sanitize_number
from fts_web.errors import (FtsParserMinRowError, FtsParserMaxRowError,
                            FtsParserOpenFileError, FtsParserCsvDelimiterError)
from fts_web.tests.utiles import FTSenderBaseTest
from fts_web.models import BaseDatosContacto


class GetDialectTest(FTSenderBaseTest):
    def test_cantidad_minima_de_filas(self):
        planilla = self.get_test_resource("planilla-ejemplo-2.csv")
        parser = ParserCsv()
        with self.assertRaises(FtsParserMinRowError):
            parser._get_dialect(open(planilla, 'r'))

    def test_delimiter_incorrecto(self):
        parser = ParserCsv()

        with self.assertRaises(FtsParserCsvDelimiterError):
            planilla = self.get_test_resource("planilla-ejemplo-5.csv")
            parser._get_dialect(open(planilla, 'r'))


class ParserCsvReadFileTests(FTSenderBaseTest):
    """Unit tests de ParserCsv.read_file()"""

    def test_generador_devuelve_datos(self):
        """
        Se crea este test debido a que la función zip() en caso que el
        generator de read_file no devuelva datos no falla, y, los test pasarán
        cuando no deberían. Testeando que el generator de read_file devuelva
        el primer dato correcto nos aseguramos que los demás test pasen
        correctamente.
        """

        parser = ParserCsv()
        planilla = self.get_test_resource("planilla-ejemplo-3.csv")
        datos_parseados = parser.read_file(0, [], [], open(planilla, 'r'))

        self.assertEqual(next(datos_parseados),
                         ['3543009865', 'lkasdjlfkaf', '0351156219387'])

    def test_devuelve_datos_correctos(self):

        lista_datos = [['3543009865', 'lkasdjlfkaf', '0351156219387'],
                       ['111534509230', 'dkasjflkja', '0351156982639'],
                       ['2830173491', 'alsdkjfieasdf', '3516983419'],
                       ['3560127341', 'kahvuahdsfasdfa', '2954638961']]

        # -----

        parser = ParserCsv()
        planilla = self.get_test_resource("planilla-ejemplo-1.csv")
        datos_parseados = parser.read_file(0, [], [], open(planilla, 'r'))

        for parseados, dato in zip(datos_parseados, lista_datos):
            self.assertEqual(parseados, dato)

    def test_datos_en_una_columna_sin_delimitador(self):

        lista_datos = [['35430098657'],
                       ['11153450923'],
                       ['28301734914'],
                       ['35601273413']]

        # -----

        parser = ParserCsv()
        planilla = self.get_test_resource("planilla-ejemplo-4.csv")
        datos_parseados = parser.read_file(0, [], [], open(planilla, 'r'))

        for parseados, dato in zip(datos_parseados, lista_datos):
            self.assertEqual(parseados, dato)

    def test_datos_sin_fila_de_titulos(self):

        lista_datos = [['3543009865', 'lkasdjlfkaf'],
                       ['111534509230', 'dkasjflkja'],
                       ['2830173491', 'alsdkjfieasdf'],
                       ['3560127341', 'kahvuahdsfasdfa']]

        # -----

        parser = ParserCsv()
        planilla = self.get_test_resource("planilla-ejemplo-0.csv")
        datos_parseados = parser.read_file(0, [], [], open(planilla, 'r'))

        for parseados, dato in zip(datos_parseados, lista_datos):
            self.assertEqual(parseados, dato)

    def test_datos_validos_y_datos_invalidos(self):
        """Test de csv con datos válidos y datos no válidos.
        Testea que no importe datos inválidos.
        """

        lista_datos = [['3543009865', 'lkasdjlfkaf', '0351156219387'],
                       ['111534509230', 'dkasjflkja', '0351156982639'],
                       ['2830173491', 'alsdkjfieasdf', '3516983419'],
                       ['3560127341', 'kahvuahdsfasdfa', '2954638961'],
                       ['283091', 'alsdkjfieasdf', '351619'],
                       ['127341', 'kahvuahdsfasdfa', '295463']]

        cantidad_datos_validos = 4

        # -----

        parser = ParserCsv()
        planilla = self.get_test_resource("planilla-ejemplo-3.csv")
        datos_parseados = parser.read_file(0, [], [], open(planilla, 'r'))

        cantidad_parseados = 0
        for parseados, dato in zip(datos_parseados, lista_datos):
            cantidad_parseados += 1
            self.assertEqual(parseados, dato)

        self.assertEqual(cantidad_parseados, cantidad_datos_validos)

    @override_settings(FTS_MAX_CANTIDAD_CONTACTOS=2)
    def test_limite_max_importacion(self):
        lista_datos = [['3543009865', 'lkasdjlfkaf', '0351156219387'],
                       ['111534509230', 'dkasjflkja', '0351156982639'],
                       ['2830173491', 'alsdkjfieasdf', '3516983419'],
                       ['3560127341', 'kahvuahdsfasdfa', '2954638961']]

        # -----

        parser = ParserCsv()
        planilla = self.get_test_resource("planilla-ejemplo-1.csv")
        datos_parseados = parser.read_file(0, [], [], open(planilla, 'r'))

        with self.assertRaises(FtsParserMaxRowError):
            for parseados, dato in zip(datos_parseados, lista_datos):
                self.assertEqual(parseados, dato)


class ValidateNumberTest(FTSenderBaseTest):
    def test_validate_number_validos(self):

        datos = ['35430098657', '(11)153450923', '28301734914', '356-01273413']

        for dato in datos:
            self.assertTrue(validate_number(dato))

    def test_validate_number_invalidos(self):

        datos = ['35445', '(11)1534509gt', '5', 'test']

        for dato in datos:
            self.assertFalse(validate_number(dato))


class SanitizeNumberTest(FTSenderBaseTest):
    def test_sanitize_number(self):
        self.assertEqual(sanitize_number('(0351)15-3368309'), '0351153368309')
