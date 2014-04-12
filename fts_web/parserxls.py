# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging

import xlrd


logger = logging.getLogger('ParserXls')


class ParserXls(object):
    """Clase utilitaria para obtener datos de archivo XLS"""

    def __init__(self):
        self.vacias = 0
        self.erroneas = 0

    def read_file(self, columna_datos, xls_file):
        """Lee un archivo XLS y devuelve contenidos de la 1er columna
        de la primer hoja.

        Parametros:
         - columna_datos: Entero que indica cuál es la
           columna con los teléfonos.
         - xls_file: archivo (ya abierto) de Excel
        """
        # Reseteamos estadisticas
        self.vacias = 0
        self.erroneas = 0
        value_list = []
        workbook = xlrd.open_workbook(file_contents=xls_file.read())
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

    def get_file_structure(self, xls_file):
        """
        Lee un archivo XLS y devuelve contenidos de
        las tres primeras filas de la primer hoja.

        Parametros:
         - xls_file: archivo (ya abierto) de Excel
        """

        structure_dic = {}

        workbook = xlrd.open_workbook(file_contents=xls_file.read())
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
