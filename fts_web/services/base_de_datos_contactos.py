# -*- coding: utf-8 -*-

"""
Servicio encargado de validar y crear las bases de datos.
"""

from __future__ import unicode_literals

from __builtin__ import callable, enumerate
import json
import logging
import os
import re

from fts_web.errors import FtsArchivoImportacionInvalidoError, FtsError, \
    FtsParserMaxRowError, FtsParserCsvImportacionError
from fts_web.models import BaseDatosContacto, Contacto, \
    MetadataBaseDatosContactoDTO
from fts_web.parser import ParserCsv, validate_telefono, validate_fechas, \
    validate_horas


logger = logging.getLogger(__name__)


class CreacionBaseDatosService(object):

    def genera_base_dato_contacto(self, base_datos_contacto):
        """
        Primer paso de la creación de una BaseDatoContacto.

        Este método se encarga de validar los datos para la creación del
        del objeto y llevar a cabo el guardado del mismo.

        Valida:
            Que el archivo subido para importar la base de datos de contactos
            sea y tenga las características válidas.
            Si el archivo es válido, hace el save del objeto y si no los es
            lanza la excepción correspondiente.
        """
        assert (base_datos_contacto.estado ==
                BaseDatosContacto.ESTADO_EN_DEFINICION)

        csv_extensions = ['.csv']

        filename = base_datos_contacto.nombre_archivo_importacion
        extension = os.path.splitext(filename)[1].lower()
        if extension not in csv_extensions:
            logger.warn("La extensión %s no es CSV. ", extension)
            raise(FtsArchivoImportacionInvalidoError("El archivo especificado "
                  "para realizar la importación de contactos no es válido"))

        base_datos_contacto.save()

    def guarda_metadata(self, base_datos_contacto):
        """
        Segundo paso de la creación de una BaseDatosContacto.

        Este método se encarga de actualizar el objeto BaseDatoContacto con
        la metadata.
        """

        base_datos_contacto.save()

    def importa_contactos(self, base_datos_contacto):
        """
        Tercer paso de la creación de una BaseDatosContacto.

        Este método se encarga de generar los objectos Contacto por cada linea
        del archivo de importación especificado para la base de datos de
        contactos.
        """
        assert (base_datos_contacto.estado ==
                BaseDatosContacto.ESTADO_EN_DEFINICION)

        metadata = base_datos_contacto.get_metadata()

        # Antes que nada, borramos los contactos preexistentes
        base_datos_contacto.elimina_contactos()

        parser = ParserCsv()

        try:
            generador_contactos = parser.read_file(base_datos_contacto)

            cantidad_contactos = 0
            for lista_dato in generador_contactos:
                cantidad_contactos += 1
                Contacto.objects.create(
                    datos=json.dumps(lista_dato),
                    bd_contacto=base_datos_contacto,
                )
        except FtsParserMaxRowError:
            base_datos_contacto.elimina_contactos()
            raise

        except FtsParserCsvImportacionError:
            base_datos_contacto.elimina_contactos()
            raise

        base_datos_contacto.cantidad_contactos = cantidad_contactos
        base_datos_contacto.save()

    def define_base_dato_contacto(self, base_datos_contacto):
        """
        Último paso de la creación de una BaseDatosContacto.

        Este método se encarga de marcar como definida y lista para su uso a
        la BaseDatosContacto.
        """
        base_datos_contacto.define()

    def inferir_metadata(self, base_datos_contacto):
        """Devuelve instancia de MetadataBaseDatosContactoDTO que describe
        la metadata del archivo desde el cual se creará la BD.

        :raises: NoSePuedeInferirMetadataError: si no se pudo inferir. Esto
                 es algo grave, ya que si se lanza es porque no se encontro
                 ninguna columan con datos que validen como telefono!
        """
        lineas = [
                  ["Nombre", "Contacto", "Email"],
                  ["juan", "549351444444", "juan@example.com"],
                  ["juan", "549351444444", "juan@example.com"],
                  ["juan", "549351444444", "juan@example.com"],
                  ]
        service = PredictorMetadataService()
        return service.inferir_metadata_desde_lineas(lineas)


class NoSePuedeInferirMetadataError(FtsError):
    """Indica que no se puede inferir los metadatos"""
    pass


DOUBLE_SPACES = re.compile(r' +')

REGEX_NOMBRE_DE_COLUMNA_VALIDO = re.compile(r'^[A-Z0-9_]+$')


class PredictorMetadataService(object):
    """
    Obtener/Adivinar/Predecir/Inferir cuál es la columna con el teléfono,
    fecha, hora.
    Generar la metadata que representara esto datos de la BDC.
    """

    def _inferir_columnas(self, lineas, func_validadora):
        assert callable(func_validadora)

        matriz = []
        for linea in lineas:
            matriz.append([
                           func_validadora(celda)
                           for celda in linea
                           ])

        # https://stackoverflow.com/questions/4937491/\
        #    matrix-transpose-in-python
        matriz_transpuesta = zip(*matriz)
        resultado_validacion_por_columna = [all(lista)
                                            for lista in matriz_transpuesta]

        return [index
                for index, value in enumerate(resultado_validacion_por_columna)
                if value]

    def sanear_nombre_de_columna(self, nombre):
        """Realiza saneamiento básico del nombre de la columna. Con basico
        se refiere a:
        - eliminar trailing spaces
        - pasar a mayusculas
        - reemplazar espacios por '_'

        Los caracteres invalidos NO son borrados.
        """
        nombre = nombre.strip().upper()
        nombre = DOUBLE_SPACES.sub("_", nombre)
        return nombre

    def validar_nombre_de_columna(self, nombre):
        """Devuelve True si el nombre de columna es valido"""
        return REGEX_NOMBRE_DE_COLUMNA_VALIDO.match(nombre)

    def inferir_metadata_desde_lineas(self, lineas):
        """
        """
        assert isinstance(lineas, (list, tuple))

        logger.debug("inferir_metadata_desde_lineas(): %s", lineas)

        if len(lineas) < 2:
            logger.debug("Se deben proveer al menos 2 lineas: %s", lineas)
            raise(NoSePuedeInferirMetadataError("Se deben proveer al menos 2 "
                                                "lineas para poder inferir "
                                                "los metadatos"))

        # Primero chequeamos q' haya igual cant. de columnas
        set_cant_columnas = set([len(linea) for linea in lineas])
        if len(set_cant_columnas) != 1:
            logger.debug("Distintas cantidades "
                         "de columnas: %s", set_cant_columnas)
            raise(NoSePuedeInferirMetadataError("Las lineas recibidas "
                                                "poseen distintas cantidades "
                                                "de columnas"))

        primer_linea = lineas[0]
        otras_lineas = lineas[1:]
        metadata = MetadataBaseDatosContactoDTO()

        # Ahora chequeamos que haya al menos 1 columna
        if len(primer_linea) == 0:
            logger.debug("Las lineas no poseen ninguna "
                         "columna: %s", primer_linea)
            raise(NoSePuedeInferirMetadataError("Las lineas no poseen ninguna "
                                                "columna"))

        metadata.cantidad_de_columnas = len(primer_linea)

        #======================================================================
        # Primero detectamos columnas de datos
        #======================================================================

        columnas_con_telefonos = self._inferir_columnas(
            otras_lineas, validate_telefono)

        logger.debug("columnas_con_telefonos: %s", columnas_con_telefonos)

        columnas_con_fechas = self._inferir_columnas(
            otras_lineas, lambda x: validate_fechas([x]))

        logger.debug("columnas_con_fechas: %s", columnas_con_fechas)

        columnas_con_horas = self._inferir_columnas(
            otras_lineas, lambda x: validate_horas([x]))

        logger.debug("columnas_con_horas: %s", columnas_con_horas)

        columna_con_telefono = None
        if len(columnas_con_telefonos) == 0:
            logger.debug("No se encontro columna con telefono")

        else:
            # Se detecto 1 o mas columnas con telefono. Usamos la 1ra.
            logger.debug("Se detecto: columnas_con_telefonos: %s",
                         columnas_con_telefonos)

            if columnas_con_telefonos[0] in columnas_con_fechas:
                logger.warn("La columna con telefono tambien esta entre "
                            "las columnas detectadas como fecha")

            elif columnas_con_telefonos[0] in columnas_con_horas:
                logger.warn("La columna con telefono tambien esta entre "
                            "las columnas detectadas como hora")
            else:
                columna_con_telefono = columnas_con_telefonos[0]

        if columna_con_telefono is not None:
            metadata.columna_con_telefono = columna_con_telefono

        metadata.columnas_con_fecha = columnas_con_fechas
        metadata.columnas_con_hora = columnas_con_horas

        # Si no hemos inferido nada, salimos
        if columna_con_telefono is None:
            # En realidad, al menos el numero de columans debio ser
            # inferido. Pero si ni siquiera se detecto numero de
            # telefono, se debe a que (a) hay un bug en esta logica
            # (b) la BD es invalida. Asi que, de cualquire manera,
            # no creo q' valga la pena devolver la instancia de mentadata,
            # me parece mas significativo reportar el hecho de que
            # no se pudo inferir el metadato.
            raise(NoSePuedeInferirMetadataError("No se pudo inferir ningun "
                                                "tipo de dato"))

        #======================================================================
        # Si detectamos telefono, fecha u hora podemos verificar si la
        #  primer linea es encabezado o dato
        #======================================================================

        validaciones_primer_linea = []

        if columna_con_telefono is not None:
            validaciones_primer_linea.append(
                validate_telefono(primer_linea[columna_con_telefono]))

        for col_fecha in metadata.columnas_con_fecha:
            validaciones_primer_linea.append(
                validate_fechas([
                                 primer_linea[col_fecha]
                                 ]))

        for col_hora in metadata.columnas_con_hora:
            validaciones_primer_linea.append(
                validate_horas([
                                primer_linea[col_hora]
                                ]))

        assert validaciones_primer_linea
        logger.debug("validaciones_primer_linea: %s",
                     validaciones_primer_linea)

        primera_fila_es_dato = all(validaciones_primer_linea)
        metadata.primer_fila_es_encabezado = not primera_fila_es_dato

        nombres = []
        if metadata.primer_fila_es_encabezado:
            nombres_orig = [x.strip() for x in primer_linea]
            for num, nombre_columna in enumerate(nombres_orig):
                nombre_columna = self.sanear_nombre_de_columna(nombre_columna)

                # si no hay nombre, le asignamos un nombre generico
                if not nombre_columna:
                    nombre_columna = self.sanear_nombre_de_columna(
                        "COLUMNA_{0}".format(num + 1))

                # revisamos q' no se repita con los preexistentes
                while nombre_columna in nombres:
                    nombre_columna = self.sanear_nombre_de_columna(
                        nombre_columna + "_REPETIDO")

                nombres.append(nombre_columna)

        else:
            nombres = [
                self.sanear_nombre_de_columna("Columna {0}".format(num + 1))
                for num in range(metadata.cantidad_de_columnas)
            ]

        metadata.nombres_de_columnas = nombres

        return metadata
