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

    def read_file(self, xls_file):
        """Lee un archivo XLS y devuelve contenidos de la 1er columna
        de la primer hoja.
        
        Parametros:
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
            cell = worksheet.cell(curr_row, 0)
            
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
