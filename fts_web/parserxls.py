# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import os
import xlrd
import csv


logger = logging.getLogger('ParserXls')


csv_extensions = ['.csv']
xls_extensions = ['.xls']


def autodetectar_parser(filefield):
    """Devuelve instancia de ParserXxx dependiendo de la
    extensión del archivo
    """

    extension = os.path.splitext(filefield.name)[1]
    if extension in xls_extensions:
        return ParserXls()
    elif extension in csv_extensions:
        return ParserCsv()
    else:
        logger.warn("El archivo %s no es CSV ni XLS. "
            "Devolveremos CSV por las dudas...", filefield.name)
        return ParserCsv()


class Parser(object):
    def __init__(self, file):
        self.file = file
        self.file_extension = None

        self._XLS = 0
        self._CSV = 1
        self._csv_extensions = ['.csv']
        self._xls_extensions = ['.xls']

        extension = os.path.splitext(self.file.name)[1]

        if extension in self._xls_extensions:
            self.file_extension = self._XLS
        elif extension in self._csv_extensions:
            self.file_extension = self._CSV

    def read_file(self, columna_datos):
        if self.file_extension == self._XLS:
            return ParserXls(self.file).read_file(columna_datos)
        elif self.file_extension == self._CSV:
            return ParserCsv(self.file).read_file(columna_datos)
        else:
            return []

    def get_file_structure(self):
        if self.file_extension == self._XLS:
            return ParserXls(self.file).get_file_structure()
        elif self.file_extension == self._CSV:
            return ParserCsv(self.file).get_file_structure()
        else:
            return {}


class ParserXls(object):
    """
    Clase utilitaria para obtener datos de archivo XLS.
    """

    def __init__(self, file):
        self.file = file
        self.vacias = 0
        self.erroneas = 0

    def read_file(self, columna_datos):
        """
        Lee un archivo XLS y devuelve contenidos de la columna
        tomada por parámetro.

        Parametros:
         - columna_datos: Entero que indica la columna con los teléfonos.
        """
        # Reseteamos estadisticas
        self.vacias = 0
        self.erroneas = 0
        value_list = []
        workbook = xlrd.open_workbook(file_contents=self.file.read())
        worksheet = workbook.sheet_by_index(0)

        num_rows = worksheet.nrows - 1
        curr_row = -1

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

            value_list.append(cell_value)

        logger.info("%s contactos importados - %s celdas ignoradas"
            " - %s celdas erroneas", len(value_list), self.vacias,
            self.erroneas)

        return value_list

    def get_file_structure(self):
        """
        Lee un archivo XLS y devuelve contenidos de
        las tres primeras filas de la primer hoja.
        """

        structure_dic = {}

        workbook = xlrd.open_workbook(file_contents=self.file.read())
        worksheet = workbook.sheet_by_index(0)

        num_rows = worksheet.nrows - 1
        num_cols = worksheet.ncols - 1

        rango = min(num_rows, 3)

        for curr_row in range(rango):
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


class ParserCsv(object):
    """
    Clase utilitaria para obtener datos de archivo CSV.
    """

    def __init__(self, file):
        self.file = file
        self.vacias = 0
        self.erroneas = 0

    def read_file(self, columna_datos):
        """
        Lee un archivo CSV y devuelve contenidos de la columna
        tomada por parámetro.

        Parametros:
         - columna_datos: Entero que indica la columna con los teléfonos.
        """
        # Reseteamos estadisticas
        self.vacias = 0
        self.erroneas = 0
        value_list = []

        workbook = csv.reader(self.file)
        for i, curr_row in enumerate(workbook):
            if not len(curr_row) == 0:
                value = curr_row[columna_datos].strip()
                if not len(value) == 0:
                    value_list.append(value)
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

    def get_file_structure(self):
        """
        Lee un archivo CSV y devuelve contenidos de
        las primeras tres filas.
        """
        workbook = csv.reader(self.file)
        structure_dic = {}

        for i in range(3):
            try:
                row = workbook.next()
                structure_dic.update({i: row})
            except:
                pass

        return structure_dic
