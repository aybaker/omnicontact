# -*- coding: utf-8 -*-

"""
Parser de archivos CSV.
"""

from __future__ import unicode_literals

import csv
import logging
import os
import re
import xlrd

from django.conf import settings

from fts_web.errors import (FtsParserCsvDelimiterError,
                            FtsParserMinRowError, FtsParserMaxRowError,
                            FtsParserOpenFileError)

logger = logging.getLogger('ParserCsv')


# =============================================================================
# Parser CSV
# =============================================================================


class ParserCsv(object):
    """
    Clase utilitaria para obtener datos de archivo CSV.
    """

    def __init__(self):
        # No es thread-safe!
        self.vacias = 0
        self.erroneas = 0

    def read_file(self, columna_con_telefono, file_obj):
        """
        Lee un archivo CSV y devuelve contenidos de la columna
        tomada por parámetro.

        Parametros:
        - columna_con_telefono: Número columna donde se encuantran los
                                teléfonos.
        - file_obj: Objeto archivo de la instancia de BaseDatosContactos.
        """
        # Reseteamos estadisticas
        self.vacias = 0
        self.erroneas = 0

        workbook = csv.reader(file_obj, self._get_dialect(file_obj))

        cantidad_importados = 0
        for i, curr_row in enumerate(workbook):
            if i > settings.FTS_MAX_CANTIDAD_CONTACTOS:
                raise FtsParserMaxRowError("El archivo CSV "
                                           "posee mas registros de los "
                                           "permitidos.")
            if i == 0 and not validate_number(curr_row[columna_con_telefono]):
                continue

            if not len(curr_row) == 0:
                value = sanitize_number(curr_row[columna_con_telefono].strip())

                if not len(value) == 0:
                    if validate_number(value):
                        cantidad_importados += 1
                        yield curr_row
                    else:
                        logger.info("Ignorando número %s, no valida "
                                    "como número telefónico.", value)
                        self.erroneas += 1
                        continue
                else:
                    logger.info("Ignorando valor vacio en fila %s", i)
                    self.vacias += 1
                    continue
            else:
                logger.info("Ignorando fila vacia %s", i)
                self.erroneas += 1

        logger.info("%s contactos importados - %s valores ignoradas"
                    " - %s celdas erroneas", cantidad_importados, self.vacias,
                    self.erroneas)

    def get_file_structure(self, file_obj):
        """
        Lee un archivo CSV y devuelve contenidos de
        las primeras tres filas.
        """

        workbook = csv.reader(file_obj, self._get_dialect(file_obj))

        i = 0
        structure_dic = {}
        for i, row in enumerate(workbook):
            if row:
                structure_dic.update({i: row})

            if i == 3:
                break

        if i < 3:
            logger.warn("El archivo CSV seleccionado posee menos de 3 "
                        "filas.")
            raise FtsParserMinRowError("El archivo CSV posee menos de "
                                       "3 filas")
        return structure_dic

    def _get_dialect(self, file_obj):
        try:
            dialect = csv.Sniffer().sniff(file_obj.read(1024),
                                          [',', ';', '\t'])
            file_obj.seek(0, 0)

            return dialect
        except csv.Error:
            file_obj.seek(0, 0)

            workbook = csv.reader(file_obj)
            single_column = []

            i = 0
            for i, row in enumerate(workbook):
                value = row[0].strip()
                try:
                    int(value)
                    value_valid = True
                except ValueError:
                    value_valid = False

                if i == 0 and not value_valid:
                    continue

                single_column.append(value_valid)

                if i == 3:
                    break

            if i < 3:
                logger.warn("El archivo CSV seleccionado posee menos de 3 "
                            "filas.")
                raise FtsParserMinRowError("El archivo CSV posee menos de "
                                           "3 filas")

            if single_column and all(single_column):
                return None

            logger.warn("No se pudo determinar el delimitador del archivo CSV")
            raise FtsParserCsvDelimiterError("No se pudo determinar el "
                                             "delimitador del archivo CSV")


# =============================================================================
# Funciones utilitarias
# =============================================================================

def validate_number(number):
    number = re.sub("[^0-9]", "", str(number))
    if re.match("^[0-9]{10,13}$", number):
        return True
    return False


def sanitize_number(number):
    return re.sub("[^0-9]", "", str(number))
