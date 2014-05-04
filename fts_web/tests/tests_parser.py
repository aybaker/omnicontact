# -*- coding: utf-8 -*-

"""Tests generales"""

from __future__ import unicode_literals

from fts_web.errors import FtsParserMinRowError, FtsParserOpenFileError, \
    FtsParserCsvDelimiterError
from fts_web.parser import ParserXls, autodetectar_parser, ParserCsv
from fts_web.tests.utiles import FTSenderBaseTest


class ParserXlsTest(FTSenderBaseTest):
    """Clase para testear parse de XLS"""

    def test_autodetectar_parser(self):
        self.assertTrue(isinstance(autodetectar_parser('file.xls'),
            ParserXls))
        self.assertTrue(isinstance(autodetectar_parser('file.csv'),
            ParserCsv))
        self.assertTrue(isinstance(autodetectar_parser('file.txt'),
            ParserCsv))
        self.assertTrue(isinstance(autodetectar_parser('file.exe'),
            ParserCsv))

    def test_planilla_ejemplo_0(self):
        """
        Test de planilla con fila de títulos y no datos.
        """

        DATOS = ['3513368309', '351153368309', '3516985862',
        '3416590872', '111545983749', '2964426445']

        planilla = self.get_test_resource("planilla-ejemplo-0.xls")
        parser = autodetectar_parser(planilla)
        datos_parseados = parser.read_file(0, open(planilla, 'r'))
        self.assertListEqual(datos_parseados, DATOS)

    def test_planilla_ejemplo_1(self):
        """Test de planilla de calculo con datos"""
        DATOS = ['3513368309', '351153368309', '3516985862',
        '3416590872', '111545983749', '2964426445']

        planilla = self.get_test_resource("planilla-ejemplo-1.xls")
        parser = autodetectar_parser(planilla)
        datos_parseados = parser.read_file(0, open(planilla, 'r'))
        self.assertListEqual(datos_parseados, DATOS)

    def test_planilla_ejemplo_2(self):
        """Test de planilla de calculo SIN datos"""

        planilla = self.get_test_resource("planilla-ejemplo-2.xls")
        parser = autodetectar_parser(planilla)
        with self.assertRaises(FtsParserMinRowError):
            parser.read_file(0, open(planilla, 'r'))

    def test_planilla_ejemplo_3(self):
        """Test de planilla de calculo con datos en varias columnas.
        Solo los datos de la primera columa son devueltos.
        """
        DATOS = ['1155890084', '3519856478', '3415268795']

        planilla = self.get_test_resource("planilla-ejemplo-3.xls")
        parser = autodetectar_parser(planilla)
        datos_parseados = parser.read_file(0, open(planilla, 'r'))
        self.assertListEqual(datos_parseados, DATOS)

    def test_planilla_ejemplo_3_columna_2(self):
        """Test de planilla de calculo con datos en varias columnas.
        Solo los datos de la segunda columa son devueltos.
        """
        DATOS = ['2218377734', '2215478630', '2213502468']

        planilla = self.get_test_resource("planilla-ejemplo-3.xls")
        parser = autodetectar_parser(planilla)
        datos_parseados = parser.read_file(1, open(planilla, 'r'))
        self.assertListEqual(datos_parseados, DATOS)

    def test_planilla_invalida_datos_random(self):
        """Test de planilla de calculo invalida (ej: corrupta)"""
        planilla = self.get_test_resource("planilla-invalida-datos-random.xls")
        parser = autodetectar_parser(planilla)
        with self.assertRaises(FtsParserOpenFileError):
            parser.read_file(0, open(planilla, 'r'))

    def test_planilla_valida_truncada(self):
        """Test de planilla de calculo truncada.
        O sea, una planilla valida, pero que le faltan bytes al final,
        emulando algun problema en la copia del archivo
        """
        planilla = self.get_test_resource("planilla-valida-truncada.xls")
        parser = autodetectar_parser(planilla)
        # No se cual, pero algun tipo de excepcion debe generarse
        # al leer un archivo truncado
        with self.assertRaises(Exception):
            parser.read_file(0, open(planilla, 'r'))

    def test_planilla_ejemplo_4(self):
        """Test de planilla de calculo con datos válidos y
        datos no válidos. Testea que no importe datos inválidos.
        """
        DATOS = ['1155890084', '3519856478', '3415268795']

        planilla = self.get_test_resource("planilla-ejemplo-4.xls")
        parser = autodetectar_parser(planilla)
        datos_parseados = parser.read_file(0, open(planilla, 'r'))
        self.assertListEqual(datos_parseados, DATOS)

    def test_planilla_ejemplo_0_csv(self):
        """Test de CSV con datos"""

        DATOS = ['3543009865', '111534509230', '2830173491', '3560127341']

        planilla = self.get_test_resource("planilla-ejemplo-0.csv")
        parser = autodetectar_parser(planilla)
        datos_parseados = parser.read_file(0, open(planilla, 'r'))

        self.assertListEqual(datos_parseados, DATOS)

    def test_planilla_ejemplo_1_csv(self):
        """Test de CSV con datos"""

        DATOS_1 = ['3543009865', '111534509230', '2830173491', '3560127341']
        DATOS_2 = ['0351156219387', '0351156982639', '3516983419',
            '2954638961']

        planilla = self.get_test_resource("planilla-ejemplo-1.csv")

        parser = autodetectar_parser(planilla)
        datos_parseados = parser.read_file(0, open(planilla, 'r'))
        self.assertListEqual(datos_parseados, DATOS_1)

        datos_parseados = parser.read_file(2, open(planilla, 'r'))
        self.assertListEqual(datos_parseados, DATOS_2)

    def test_planilla_ejemplo_2_csv(self):
        """Test de CSV SIN datos"""

        planilla = self.get_test_resource("planilla-ejemplo-2.csv")
        parser = autodetectar_parser(planilla)
        with self.assertRaises(FtsParserCsvDelimiterError):
            parser.read_file(0, open(planilla, 'r'))

    def test_planilla_ejemplo_3_csv(self):
        """Test de csv con datos válidos y datos no válidos.
        Testea que no importe datos inválidos.
        """

        DATOS = ['3543009865', '111534509230', '2830173491', '3560127341']

        planilla = self.get_test_resource("planilla-ejemplo-3.csv")

        parser = autodetectar_parser(planilla)
        datos_parseados = parser.read_file(0, open(planilla, 'r'))
        self.assertListEqual(datos_parseados, DATOS)
