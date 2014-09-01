# -*- coding: utf-8 -*-

"""
Servicio encargado de validar y crear las bases de datos.
"""

from __future__ import unicode_literals

import os
import json
import logging

from fts_web.errors import FtsArchivoImportacionInvalidoError
from fts_web.models import BaseDatosContacto, Contacto
from fts_web.parser import ParserCsv


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
        csv_extensions = ['.csv']

        filename = base_datos_contacto.nombre_archivo_importacion
        extension = os.path.splitext(filename)[1].lower()
        if extension not in csv_extensions:
            logger.warn("La extensión %s no es CSV. ", extension)
            raise(FtsArchivoImportacionInvalidoError("El archivo especificado "
                  "para realizar la importación de contactos no es válido"))

        base_datos_contacto.save()

    def guarda_metadata(self, base_datos_contacto, dic_metadata):
        """
        Segundo paso de la creación de una BaseDatosContacto.

        Este método se encarga de actualizar el objeto BaseDatoContacto con
        la metadata.
        Parametros:
        - base_datos_contacto: La instancia de BaseDatosContacto que se
                               actualiza.
        - dic_metadata: Diccionario con los datos extras de la metadata. La
                        clave es el atributo y el valor, el valor que
                        corresponde.
        """
        metadata = base_datos_contacto.get_metadata()

        for propiedad, valor in dic_metadata.items():
            setattr(metadata, propiedad, valor)

        base_datos_contacto.save()

    def importa_contactos(self, base_datos_contacto):
        """
        Tercer paso de la creación de una BaseDatosContacto.

        Este método se encarga de generar los objectos Contacto por cada linea
        del archivo de importación especificado para la base de datos de
        contactos.
        """
        base_datos_metadata = base_datos_contacto.get_metadata()
        columna_con_telefono = base_datos_metadata.columna_con_telefono

        parser = ParserCsv()
        generador_contactos = parser.read_file(
            columna_con_telefono, base_datos_contacto.archivo_importacion.file)

        cantidad_contactos = 0
        for lista_dato in generador_contactos:
            cantidad_contactos += 1
            Contacto.objects.create(
                datos=json.dumps(lista_dato),
                bd_contacto=base_datos_contacto,
            )

        base_datos_contacto.cantidad_contactos = cantidad_contactos
        base_datos_contacto.save()

    def define_base_dato_contacto(self, base_datos_contacto):
        """
        Último paso de la creación de una BaseDatosContacto.

        Este método se encarga de marcar como definida y lista para su uso a
        la BaseDatosContacto.
        """
        base_datos_contacto.define()
