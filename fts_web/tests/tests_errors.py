# -*- coding: utf-8 -*-

"""Tests del modulo fts_web.errors"""

from __future__ import unicode_literals

from fts_web.errors import FtsAudioConversionError, FtsParserCsvImportacionError
from fts_web.tests.utiles import FTSenderBaseTest


class ErrorsTest(FTSenderBaseTest):

    def test_exceptions(self):
        try:
            raise FtsAudioConversionError()
        except FtsAudioConversionError as e:
            self.assertEqual(str(e), "")

        try:
            raise FtsAudioConversionError("mensaje")
        except FtsAudioConversionError as e:
            self.assertEqual(str(e), "mensaje")

        try:
            try:
                {}['err']
            except KeyError as keyerr:
                raise FtsAudioConversionError("mensaje")
        except FtsAudioConversionError as e:
            self.assertEqual(str(e), "mensaje")

        try:
            try:
                {}['err']
            except KeyError as keyerr:
                raise FtsAudioConversionError("mensaje", cause=keyerr)
        except FtsAudioConversionError as e:
            self.assertEqual(str(e), "mensaje (caused by "
                "<type 'exceptions.KeyError'>: u'err')")

        try:
            try:
                list()[1]
            except IndexError as err:
                raise FtsAudioConversionError("mensaje", cause=err)
        except FtsAudioConversionError as e:
            self.assertEqual(str(e), "mensaje (caused by "
                "<type 'exceptions.IndexError'>: list index out of range)")


class FtsParserCsvImportacionErrorTest(FTSenderBaseTest):

    def test_genera_correctamente_con_str_ascii(self):
        FtsParserCsvImportacionError(
                numero_fila=1,
                numero_columna='',
                fila=[b'una', b'fila', b'de', b'strings'],
                valor_celda=b'strings')

    def test_genera_correctamente_con_str_utf8(self):
        FtsParserCsvImportacionError(
                numero_fila=1,
                numero_columna='',
                fila=[b'fila', b'hol\xc3\xa1'],
                valor_celda=b'hol\xc3\xa1')

    def test_genera_correctamente_con_fila_de_str_iso_8859_2(self):
        FtsParserCsvImportacionError(
                numero_fila=1,
                numero_columna='',
                fila=[b'fila', b'hol\xe1'],
                valor_celda=b'hol\xe1')

    def test_genera_correctamente_con_fila_de_unicode(self):
        FtsParserCsvImportacionError(
                numero_fila=1,
                numero_columna='',
                fila=[u'fila', u'holá'],
                valor_celda=u'holá')
