# -*- coding: utf-8 -*-

"""
Parser de archivos CSV.
"""

from __future__ import unicode_literals

import csv
import logging
import re

from django.conf import settings
from fts_web.errors import (FtsParserCsvDelimiterError,
                            FtsParserMinRowError, FtsParserMaxRowError,
                            FtsParserCsvImportacionError)
from fts_web.models import MetadataBaseDatosContactoDTO


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

    def read_file(self, base_datos_contactos):
        """Lee un archivo CSV y devuelve contenidos de las columnas."""

        # Reseteamos estadisticas
        self.vacias = 0

        # base_datos_contactos.archivo_importacion.open()
        # file_obj = base_datos_contactos.archivo_importacion.file
        # try:
        #     return self._read_file(file_obj,
        #                            self._get_dialect(file_obj),
        #                            base_datos_contactos.get_metadata()
        #                            )
        # finally:
        #     base_datos_contactos.archivo_importacion.close()

        # with open(base_datos_contactos.archivo_importacion.path, 'rb')
        #     as file_obj:
        #     return self._read_file(file_obj,
        #                            self._get_dialect(file_obj),
        #                            base_datos_contactos.get_metadata()
        #                            )

        file_obj = base_datos_contactos.archivo_importacion.file
        return self._read_file(file_obj,
                               self._get_dialect(file_obj),
                               base_datos_contactos.get_metadata()
                               )

    def _read_file(self, file_obj, dialect, metadata):

        assert isinstance(metadata, MetadataBaseDatosContactoDTO)

        workbook = csv.reader(file_obj, dialect)

        cantidad_importados = 0
        for i, curr_row in enumerate(workbook):
            if len(curr_row) == 0:
                logger.info("Ignorando fila vacia %s", i)
                self.vacias += 1
                continue

            if i >= settings.FTS_MAX_CANTIDAD_CONTACTOS:
                raise FtsParserMaxRowError("El archivo CSV "
                                           "posee mas registros de los "
                                           "permitidos.")

            telefono = sanitize_number(
                curr_row[metadata.columna_con_telefono].strip())

            if not validate_telefono(telefono):
                if i == 0 and metadata.primer_fila_es_encabezado:
                    continue
                logger.warn("Error en la imporación de contactos: No "
                            "valida el teléfono en la linea %s",
                            curr_row)
                raise FtsParserCsvImportacionError(
                    numero_fila=i,
                    numero_columna=metadata.columna_con_telefono,
                    fila=curr_row,
                    valor_celda=telefono)

            if metadata.columnas_con_fecha:
                fechas = [curr_row[columna]
                          for columna in metadata.columnas_con_fecha]
                if not validate_fechas(fechas):
                    logger.warn("Error en la imporación de contactos: No "
                                "valida el formato fecha en la linea %s",
                                curr_row)
                    raise FtsParserCsvImportacionError(
                        numero_fila=i,
                        numero_columna=metadata.columnas_con_fecha,
                        fila=curr_row,
                        valor_celda=fechas)

            if metadata.columnas_con_hora:
                horas = [curr_row[columna]
                         for columna in metadata.columnas_con_hora]
                if not validate_horas(horas):
                    logger.warn("Error en la imporación de contactos: No "
                                "valida el formato hora en la linea %s",
                                curr_row)
                    raise FtsParserCsvImportacionError(
                        numero_fila=i,
                        numero_columna=metadata.columnas_con_hora,
                        fila=curr_row,
                        valor_celda=horas)

            cantidad_importados += 1
            yield curr_row

        logger.info("%s contactos importados - %s valores ignoradas.",
                    cantidad_importados, self.vacias)

    def previsualiza_archivo(self, base_datos_contactos):
        """
        Lee un archivo CSV y devuelve contenidos de
        las primeras tres filas.
        """

        file_obj = base_datos_contactos.archivo_importacion.file
        return self._previsualiza_archivo(file_obj)

    def _previsualiza_archivo(self, file_obj):

        workbook = csv.reader(file_obj, self._get_dialect(file_obj))

        structure_dic = []
        for i, row in enumerate(workbook):
            if row:
                structure_dic.append(row)

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

        finally:
            file_obj.seek(0, 0)


# =============================================================================
# Funciones utilitarias
# =============================================================================

def validate_fechas(fechas):
    """
    Esta función en principio, valida el formato de las fechas.
    Si todas validan devuelve True, sino False.
    """
    if not fechas:
        return False

    validate = []
    for fecha in fechas:
        if re.match(
            "^(0[1-9]|[12][0-9]|3[01])[/](0[1-9]|1[012])[/](19|20)?\d\d$",
                fecha):
            validate.append(True)
        else:
            validate.append(False)
    return all(validate)


def validate_horas(horas):
    """
    Esta función en principio, valida el formato de las horas.
    Si todas validan devuelve True, sino False.
    """
    if not horas:
        return False

    validate = []
    for hora in horas:

        if re.match(
            "^(([0-1][0-9])|([2][0-3])):([0-5]?[0-9])(:([0-5]?[0-9]))?$",
                hora):
            validate.append(True)
        else:
            validate.append(False)
    return all(validate)


def validate_telefono(number):
    """
    Esta función valida el numero telefónico tenga  entre 10 y 13 dígitos.
    """
    number = re.sub("[^0-9]", "", str(number))
    if re.match("^[0-9]{10,13}$", number):
        return True
    return False


def sanitize_number(number):
    number = unicode(number)
    return re.sub("[^0-9]", "", number)
