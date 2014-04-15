# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import csv
import logging
import os
import re
import xlrd


logger = logging.getLogger('ParserXls')


csv_extensions = ['.csv']
xls_extensions = ['.xls']


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
        value_list = []
        workbook = xlrd.open_workbook(file_contents=file_obj.read())
        worksheet = workbook.sheet_by_index(0)

        num_rows = worksheet.nrows - 1
        curr_row = -1

        if not validate_number(worksheet.cell(0, columna_datos)):
            curr_row = 0

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

    def get_file_structure(self, file_obj):
        """
        Lee un archivo XLS y devuelve contenidos de
        las tres primeras filas de la primer hoja.
        """

        structure_dic = {}

        workbook = xlrd.open_workbook(file_contents=file_obj.read())
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
        value_list = []

        read_line = file_obj.readline()
        if read_line:
            dialect = csv.Sniffer().sniff(read_line, [',', ';', '|', ' '])
            file_obj.seek(0, 0)
            workbook = csv.reader(file_obj, dialect)
            for i, curr_row in enumerate(workbook):
                if i == 0 and not validate_number(curr_row[columna_datos]):
                    continue

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

    def get_file_structure(self, file_obj):
        """
        Lee un archivo CSV y devuelve contenidos de
        las primeras tres filas.
        """

        read_line = file_obj.readline()
        if read_line:
            dialect = csv.Sniffer().sniff(read_line, [',', ';', '|', ' '])
            file_obj.seek(0, 0)
            workbook = csv.reader(file_obj, dialect)
            structure_dic = {}

            for i in range(3):
                try:
                    row = workbook.next()
                    structure_dic.update({i: row})
                except:
                    pass

        return structure_dic
