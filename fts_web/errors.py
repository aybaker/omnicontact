#-*- coding: utf-8 -*-

"""
Excepciones base del sistema.
"""

from __future__ import unicode_literals


class FtsError(Exception):
    """Excepcion base para FTS"""

    def __init__(self, message=None, cause=None):
        """Crea excepcion.
        Parametros:
            message: mensaje (opcional)
            cause: excepcion causa (opcional)
        """
        if message is None:
            super(FtsError, self).__init__()
        else:
            super(FtsError, self).__init__(message)

        self.cause = cause

        # chain_current_exception: (opcional) si es verdadero, toma
        #    el traceback actual `traceback.format_exc()` y lo guarda
        #    como texto para ser impreso en `__str__()`
        # if chain_current_exception:
        #    self.curr_exception_traceback = traceback.format_exc()
        # else:
        #    self.curr_exception_traceback = None

    def __str__(self):
        try:
            if self.cause is None:
                return super(FtsError, self).__str__()
            else:
                return "{0} (caused by {1}: {2})".format(
                    super(FtsError, self).__str__(),
                    type(self.cause),
                    str(self.cause),
                )
        except:
            return super(FtsError, self).__str__()


class FtsAudioConversionError(FtsError):
    """Error al intentar convertir audio"""
    pass


class FtsParserCsvImportacionError(FtsError):
    """
    Error en la importación de los datos del archivo csv.
    No valida alguno de los datos.
    """
    def __init__(self, numero_fila, numero_columna, fila, valor_celda):
        super(DerivacionExternaForm, self).__init__(*args, **kwargs)
        self.numero_fila = numero_fila
        self.numero_columna = numero_columna
        self.fila = fila
        self.valor_celda = valor_celda


class FtsParserCsvDelimiterError(FtsError):
    """
    Error al intentar determinar el delimitador en
    el ParserCsv.
    """
    pass


class FtsParserMinRowError(FtsError):
    """
    El archivo querido Parsear tiene menos de 3 filas.
    """
    pass


class FtsParserMaxRowError(FtsError):
    """
    El archivo querido Parsear tiene mas filas de las permitidas.
    """
    pass


class FtsParserOpenFileError(FtsError):
    """
    No se pudo abrir el archivo a Parsear
    """
    pass


class FtsRecicladoBaseDatosContactoError(FtsError):
    """
    No se pudo obtener la base de datos en el reciclado de la campana.
    """
    pass


class FtsRecicladoCampanaError(FtsError):
    """
    No se pudo generar el reciclado de la campana.
    """
    pass


class FtsDepuraBaseDatoContactoError(FtsError):
    """
    No se pudo depurar la base datos de contactos.
    """
    pass


class FtsArchivoImportacionInvalidoError(FtsError):
    """
    El archivo para realizar la importación de Contactos no es válido.
    """
    pass


class FTSOptimisticLockingError(FtsError):
    """Se intentó actualizar un objeto modificado por otro thread/proceso"""
    pass
