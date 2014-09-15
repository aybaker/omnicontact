# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.test.utils import override_settings
from fts_web.errors import (FtsParserMinRowError, FtsParserMaxRowError,
                            FtsParserCsvDelimiterError,
    FtsParserCsvImportacionError)
from fts_web.parser import ParserCsv, validate_telefono, sanitize_number, \
    validate_fechas, validate_horas
from fts_web.tests.utiles import FTSenderBaseTest, get_test_resource_directory
from fts_web.models import BaseDatosContacto, MetadataBaseDatosContactoDTO, \
    MetadataBaseDatosContacto


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

    def _get_bdc_para_planilla_ejemplo_0(self):
        """Devuelve BDC que se crea con "planilla-ejemplo-0.csv"
        """
        nombre_archivo = "planilla-ejemplo-0.csv"
        BaseDatosContacto.objects.create(nombre="test",
                                         archivo_importacion=nombre_archivo,
                                         nombre_archivo_importacion="xx.csv",
                                         metadata="")

        # Solo hay 1, get() no puede fallar
        bdc = BaseDatosContacto.objects.all().get()
        metadata = bdc.get_metadata()
        assert isinstance(metadata, MetadataBaseDatosContacto)
        metadata.cantidad_de_columnas = 4
        metadata.columna_con_telefono = 0
        metadata.columnas_con_fecha = [2]
        metadata.columnas_con_hora = [3]
        metadata.nombres_de_columnas = ["telefono_fijo",
                                        "nombre",
                                        "fecha",
                                        "hora"
                                        ]
        metadata.primer_fila_es_encabezado = True
        bdc.save()
        return bdc

    def _get_bdc_para_planilla_ejemplo_1(self):
        """Devuelve BDC que se crea con "planilla-ejemplo-1.csv"
        """
        nombre_archivo = "planilla-ejemplo-1.csv"
        BaseDatosContacto.objects.create(nombre="test",
                                         archivo_importacion=nombre_archivo,
                                         nombre_archivo_importacion="xx.csv",
                                         metadata="")

        # Solo hay 1, get() no puede fallar
        bdc = BaseDatosContacto.objects.all().get()
        metadata = bdc.get_metadata()
        assert isinstance(metadata, MetadataBaseDatosContacto)
        metadata.cantidad_de_columnas = 3
        metadata.columna_con_telefono = 0
        metadata.nombres_de_columnas = ["telefono_fijo",
                                        "nombre",
                                        "celular"]
        metadata.primer_fila_es_encabezado = False
        bdc.save()
        return bdc

    def _get_bdc_para_planilla_ejemplo_3(self):
        """Devuelve BDC que se crea con "planilla-ejemplo-3.csv".
        Usa columna '2' (3ra columna) para telefonos.
        OJO: la 5ta fila tenga un telefono invalido.
        """
        nombre_archivo = "planilla-ejemplo-3.csv"
        BaseDatosContacto.objects.create(nombre="test",
                                         archivo_importacion=nombre_archivo,
                                         nombre_archivo_importacion="xx.csv",
                                         metadata="")

        # Solo hay 1, get() no puede fallar
        bdc = BaseDatosContacto.objects.all().get()
        metadata = bdc.get_metadata()
        assert isinstance(metadata, MetadataBaseDatosContacto)
        metadata.cantidad_de_columnas = 3
        # Usamos columna '2', que es la que tiene numeros de telefonos
        #  invalidos en la 5ta fila
        metadata.columna_con_telefono = 2
        metadata.nombres_de_columnas = ["telefono_fijo",
                                        "nombre",
                                        "celular"]
        metadata.primer_fila_es_encabezado = False
        bdc.save()
        return bdc

    def _get_bdc_para_planilla_ejemplo_4(self):
        """Devuelve BDC que se crea con "planilla-ejemplo-4.csv"
        """
        nombre_archivo = "planilla-ejemplo-4.csv"
        BaseDatosContacto.objects.create(nombre="test",
                                         archivo_importacion=nombre_archivo,
                                         nombre_archivo_importacion="xx.csv",
                                         metadata="")

        # Solo hay 1, get() no puede fallar
        bdc = BaseDatosContacto.objects.all().get()
        metadata = bdc.get_metadata()
        assert isinstance(metadata, MetadataBaseDatosContacto)
        metadata.cantidad_de_columnas = 1
        metadata.columna_con_telefono = 0  # o 2?
        metadata.nombres_de_columnas = ["telefono_fijo"]
        metadata.primer_fila_es_encabezado = False
        bdc.save()
        return bdc

    @override_settings(MEDIA_ROOT=get_test_resource_directory())
    def test_devuelve_datos_correctos(self):

        datos_correctos = [['3543009865', 'lkasdjlfkaf', '0351156219387'],
                           ['111534509230', 'dkasjflkja', '0351156982639'],
                           ['2830173491', 'alsdkjfieasdf', '3516983419'],
                           ['3560127341', 'kahvuahdsfasdfa', '2954638961']]

        bdc = self._get_bdc_para_planilla_ejemplo_1()

        parser = ParserCsv()

        # -----

        self.assertListEqual(datos_correctos,
                             [_ for _ in parser.read_file(bdc)])

    @override_settings(MEDIA_ROOT=get_test_resource_directory())
    def test_datos_en_una_columna_sin_delimitador(self):

        datos_correctos = [['35430098657'],
                           ['11153450923'],
                           ['28301734914'],
                           ['35601273413']]

        bdc = self._get_bdc_para_planilla_ejemplo_4()

        parser = ParserCsv()

        # -----

        self.assertListEqual(datos_correctos,
                             [_ for _ in parser.read_file(bdc)])

    @override_settings(MEDIA_ROOT=get_test_resource_directory())
    def test_detecta_datos_invalidos(self):

        # El archivo tiene 4 lineas validas, y la 5ta es INVALIDA
        datos_correctos = [['3543009865', 'lkasdjlfkaf', '0351156219387'],
                           ['111534509230', 'dkasjflkja', '0351156982639'],
                           ['2830173491', 'alsdkjfieasdf', '3516983419'],
                           ['3560127341', 'kahvuahdsfasdfa', '2954638961'],
                           ]

        bdc = self._get_bdc_para_planilla_ejemplo_3()

        parser = ParserCsv()

        # -----

        datos_parseados = []
        with self.assertRaises(FtsParserCsvImportacionError):
            for datos_contacto in parser.read_file(bdc):
                datos_parseados.append(datos_contacto)

        # Debio devolver los primeros 4 ANTES de generar la excepcion
        self.assertEquals(len(datos_parseados), 4)

        self.assertListEqual(datos_correctos, datos_parseados)

    @override_settings(FTS_MAX_CANTIDAD_CONTACTOS=2,
                       MEDIA_ROOT=get_test_resource_directory())
    def test_limite_max_importacion(self):

        datos_correctos = [['3543009865', 'lkasdjlfkaf', '0351156219387'],
                           ['111534509230', 'dkasjflkja', '0351156982639'],
                           ]

        bdc = self._get_bdc_para_planilla_ejemplo_1()

        parser = ParserCsv()

        # -----

        datos_parseados = []
        with self.assertRaises(FtsParserMaxRowError):
            for datos_contacto in parser.read_file(bdc):
                datos_parseados.append(datos_contacto)

        # Debio devolver los primeros 2 ANTES de generar la excepcion
        self.assertEquals(len(datos_parseados), 2)

        self.assertListEqual(datos_correctos, datos_parseados)

    @override_settings(MEDIA_ROOT=get_test_resource_directory())
    def test_datos_con_fecha_excluye_invalido(self):

        datos_correctos = [
            ['3543009865', 'lkasdjlfkaf', '10/10/2014', '12:00'],
            ['111534509230', 'dkasjflkja', '10/10/2014', '12:00'],
            ['2830173491', 'alsdkjfieasdf', '10/10/2014', '12:00']
        ]

        bdc = self._get_bdc_para_planilla_ejemplo_0()
        metadata = bdc.get_metadata()
        # Cambiamos metadata, para q' ignore 'hora' y solo detecte
        #  error en 'fecha'
        metadata.columnas_con_hora = []
        bdc.save()

        parser = ParserCsv()

        # -----

        datos_parseados = []
        with self.assertRaises(FtsParserCsvImportacionError) as cm:
            for datos_contacto in parser.read_file(bdc):
                datos_parseados.append(datos_contacto)

        self.assertEquals(cm.exception.valor_celda, "fecha")

        # Debio devolver los primeros 3 ANTES de generar la excepcion
        self.assertEquals(len(datos_parseados), 3)

        self.assertListEqual(datos_correctos, datos_parseados)

    @override_settings(MEDIA_ROOT=get_test_resource_directory())
    def test_datos_con_hora_excluye_invalido(self):

        datos_correctos = [
            ['3543009865', 'lkasdjlfkaf', '10/10/2014', '12:00'],
            ['111534509230', 'dkasjflkja', '10/10/2014', '12:00'],
            ['2830173491', 'alsdkjfieasdf', '10/10/2014', '12:00']
        ]

        bdc = self._get_bdc_para_planilla_ejemplo_0()
        metadata = bdc.get_metadata()
        # Cambiamos metadata, para q' ignore 'fecha' y solo detecte
        #  error en 'hora'
        metadata.columnas_con_fecha = []
        bdc.save()

        parser = ParserCsv()

        # -----

        datos_parseados = []
        with self.assertRaises(FtsParserCsvImportacionError) as cm:
            for datos_contacto in parser.read_file(bdc):
                datos_parseados.append(datos_contacto)

        self.assertEquals(cm.exception.valor_celda, "hora")

        # Debio devolver los primeros 3 ANTES de generar la excepcion
        self.assertEquals(len(datos_parseados), 3)

        self.assertListEqual(datos_correctos, datos_parseados)


class ValidateTelefonoTest(FTSenderBaseTest):
    def test_validate_number_validos(self):

        datos = ['35430098657', '(11)153450923', '28301734914', '356-01273413']

        for dato in datos:
            self.assertTrue(validate_telefono(dato))

    def test_validate_number_invalidos(self):

        datos = ['35445', '(11)1534509gt', '5', 'test']

        for dato in datos:
            self.assertFalse(validate_telefono(dato))


class SanitizeNumberTest(FTSenderBaseTest):
    def test_sanitize_number(self):
        self.assertEqual(sanitize_number('(0351)15-3368309'), '0351153368309')


class ValidateFechasTest(FTSenderBaseTest):
    def test_validate_fechas_validos(self):
        datos = ['01/01/2014', '01/01/14', '16/07/16', '31/07/16']

        self.assertTrue(validate_fechas(datos))

    def test_validate_fechas_formato_invalidos(self):
        datos = ['1/1/2014']

        self.assertFalse(validate_fechas(datos))

    def test_validate_fechas_no_fecha(self):
        datos = ['test']

        self.assertFalse(validate_fechas(datos))

    def test_validate_fechas_vacias(self):
        datos = []

        self.assertFalse(validate_fechas(datos))


class ValidateHorasTest(FTSenderBaseTest):
    def test_validate_horas_validos(self):
        datos = ['16:00', '16:00:00', '01:00', '00:00']

        self.assertTrue(validate_horas(datos))

    def test_validate_horas_formato_invalido1(self):
        datos = ['10:00pm']

        self.assertFalse(validate_horas(datos))

    def test_validate_horas_formato_invalido2(self):
        datos = ['1:00']

        self.assertFalse(validate_horas(datos))

    def test_validate_horas_formato_invalido3(self):
        datos = ['24:00']

        self.assertFalse(validate_horas(datos))

    def test_validate_horas_no_hora(self):
        datos = ['test']

        self.assertFalse(validate_horas(datos))

    def test_validate_horas_vacias(self):
        datos = []

        self.assertFalse(validate_horas(datos))
