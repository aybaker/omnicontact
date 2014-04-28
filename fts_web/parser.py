# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import csv
import logging
import os
import re
import xlrd

from fts_web.errors import (FtsParserCsvDelimiterError,
 FtsParserMinRowError, FtsParserOpenFileError)

logger = logging.getLogger('ParserXls')


csv_extensions = ['.csv']
xls_extensions = ['.xls', '.xlsx']


def autodetectar_parser(filename):
    """Devuelve instancia de ParserXxx dependiendo de la
    extensión del archivo

    Parametros:
     - filename (str) EL nombre del archivo que subió.
    """
    extension = os.path.splitext(filename)[1].lower()
    if extension in xls_extensions:
        return ParserXls()
    elif extension in csv_extensions:
        return ParserCsv()
    else:
        logger.warn("La extensión %s no es CSV ni XLS. "
            "Devolveremos CSV por las dudas...", extension)
        return ParserCsv()


def validate_number(number):
    number = re.sub("[^0-9]", "", str(number))
    if re.match("^[0-9]{10,13}$", number):
        return True
    return False


class ParserXls(object):
    """
    Clase utilitaria para obtener datos de archivo XLS.
    """

    def __init__(self):
        # No es thread-safe!
        self.vacias = 0
        self.erroneas = 0

    def read_file(self, columna_datos, file_obj):
        """
        Lee un archivo XLS y devuelve contenidos de la columna
        tomada por parámetro.

        Parametros:
         - columna_datos: Entero que indica la columna con los teléfonos.
         - file_obj: Objeto archivo de la instancia de BaseDatosContactos.
        """

        # Reseteamos estadisticas
        self.vacias = 0
        self.erroneas = 0

        worksheet = self._get_worksheet(file_obj)
        num_rows = worksheet.nrows - 1
        curr_row = -1

        #Valida primera fila que el dato sea un número con
        #formato teléfonico.
        if not validate_number(worksheet.cell(0, columna_datos)):
            curr_row = 0

        value_list = []
        while curr_row < num_rows:
            curr_row += 1
            cell = worksheet.cell(curr_row, columna_datos)

            # Guardamos valor de nro telefonico en 'cell_value'
            if type(cell.value) == float:
                cell_value = str(int(cell.value))
            elif type(cell.value) == str:
                cell_value = cell.value.strip()
                if len(cell_value) == 0:
                    logger.info("Ignorando celda vacia en fila %s", curr_row)
                    self.vacias += 1
                    continue
            else:
                try:
                    # Intentamos convertir en string y ver que pasa...
                    cell_value = str(cell.value).strip()
                except:
                    logger.info("Ignorando celda en fila %s con valor '%s' "
                        "de tipo %s", curr_row, cell.value, type(cell.value))
                    self.erroneas += 1
                    continue

            if validate_number(cell_value):
                value_list.append(cell_value)
            else:
                logger.info("Ignorando número %s, no valida"
                    "como número telefónico.", cell.value)
                self.erroneas += 1

        logger.info("%s contactos importados - %s celdas ignoradas"
            " - %s celdas erroneas", len(value_list), self.vacias,
            self.erroneas)

        return value_list

    def get_file_structure(self, file_obj):
        """
        Lee un archivo XLS y devuelve contenidos de
        las tres primeras filas de la primer hoja.
        """

        worksheet = self._get_worksheet(file_obj)
        num_cols = worksheet.ncols - 1

        structure_dic = {}
        for curr_row in range(3):
            curr_col = -1
            row_content_list = []

            while curr_col < num_cols:
                curr_col += 1

                value = worksheet.cell_value(curr_row, curr_col)
                if type(value) == float:
                    value = str(int(value))
                row_content_list.append(value)

            structure_dic.update({curr_row: row_content_list})

        return structure_dic

    def _get_worksheet(self, file_obj):
        try:
            workbook = xlrd.open_workbook(file_contents=file_obj.read())
            worksheet = workbook.sheet_by_index(0)
        except xlrd.XLRDError as e:
            logger.warn("No se pudo abrir el archivo XLS. Excepción: %s", e)

            raise FtsParserOpenFileError("El archivo XLS seleccionado"
                " no pudo ser abierto.")

        if worksheet.nrows < 3:
            logger.warn("El archivo XLS seleccionado posee menos de 3 filas.")

            raise FtsParserMinRowError("El archivo XLS posee menos"
                " de 3 filas")
        return worksheet


class ParserCsv(object):
    """
    Clase utilitaria para obtener datos de archivo CSV.
    """

    def __init__(self):
        # No es thread-safe!
        self.vacias = 0
        self.erroneas = 0

    def read_file(self, columna_datos, file_obj):
        """
        Lee un archivo CSV y devuelve contenidos de la columna
        tomada por parámetro.

        Parametros:
        - columna_datos: Entero que indica la columna con los teléfonos.
        - file_obj: Objeto archivo de la instancia de BaseDatosContactos.
        """
        # Reseteamos estadisticas
        self.vacias = 0
        self.erroneas = 0

        workbook = csv.reader(file_obj, self._get_dialect(file_obj))

        value_list = []
        for i, curr_row in enumerate(workbook):
            if i == 0 and not validate_number(curr_row[columna_datos]):
                continue

            if not len(curr_row) == 0:
                value = curr_row[columna_datos].strip()
                if not len(value) == 0:
                    if validate_number(value):
                        value_list.append(value)
                    else:
                        logger.info("Ignorando número %s, no valida"
                            "como número telefónico.", value)
                        self.erroneas += 1
                else:
                    logger.info("Ignorando valor vacio en fila %s", i)
                    self.vacias += 1
                    continue
            else:
                logger.info("Ignorando fila vacia %s", i)
                self.erroneas += 1

        logger.info("%s contactos importados - %s valores ignoradas"
            " - %s celdas erroneas", len(value_list), self.vacias,
            self.erroneas)

        return value_list

    def get_file_structure(self, file_obj):
        """
        Lee un archivo CSV y devuelve contenidos de
        las primeras tres filas.
        """

        workbook = csv.reader(file_obj, self._get_dialect(file_obj))

        structure_dic = {}
        for i in range(3):
            row = workbook.next()
            if row:
                structure_dic.update({i: row})

        if len(structure_dic) < 3:
            logger.warn("El archivo CSV seleccionado posee menos de 3 filas.")
            raise FtsParserMinRowError("El archivo CSV "
                "posee menos de 3 filas")

        return structure_dic

    def _get_dialect(self, file_obj):
        try:
            dialect = csv.Sniffer().sniff(file_obj.read(1024), [',', ';', '\t'])
            file_obj.seek(0, 0)

            return dialect
        except csv.Error:
            logger.warn("No se pudo determinar el delimitador del archivo CSV")
            raise FtsParserCsvDelimiterError("No se pudo determinar el "
                "delimitador del archivo CSV")
