# -*- coding: utf-8 -*-

"""Tests comportamiento de libreria csv"""

from __future__ import unicode_literals

import csv

from fts_web.tests.utiles import FTSenderBaseTest


class TestCsv(FTSenderBaseTest):

    def _test_lee_como_str(self, filename):
        with open(filename, "r") as file_obj:
            csv_reader = csv.reader(file_obj)
            filas = [fila for fila in csv_reader]
            # [
            #    ['Tel\xc3\xa9fono', 'Nombre'],
            #    ['375849371648', 'Macaran\xc3\xa1'],
            #    ['957327493493', '\xe4\xbd\x90\xe8\x97\xa4']
            # ]

            self.assertEquals(len(filas), 3)
            self.assertEquals(len(filas[0]), 2)

            # validamos que todos sean str
            for fila in filas:
                for celda in fila:
                    self.assertEquals(type(celda), str)

    def test_csv_con_utf8_es_leido_como_str(self):
        filename = self.get_test_resource("csv-codificacion/"
                                          "bd-contactos-utf8.csv")

        self._test_lee_como_str(filename)

    def test_csv_con_iso_8859_es_leido_como_str(self):
        filename = self.get_test_resource("csv-codificacion/"
                                          "bd-contactos-iso-8859-2.csv")

        self._test_lee_como_str(filename)
