# -*- coding: utf-8 -*-

"""
Servicio encargado de validar y crear las bases de datos.
"""

from __future__ import unicode_literals

import logging

from fts_web.models import BaseDatosContacto


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
        #     csv_extensions = ['.csv']
        #     extension = os.path.splitext(filename)[1].lower()
        #     if extension in csv_extensions:
        #         return ParserCsv()
        #     else:
        #         logger.warn("La extensión %s no es CSV. ", extension)
        pass

    def guardar_metadata(self, base_datos_contacto, metadata):
        """
        Segundo paso de la creación de una BaseDatosContacto.

        Este método se encarga de actualizar el objeto BaseDatoContacto con
        la metadata.
        """
        pass

    def importa_contactos(self, base_datos_contacto):
        """
        Tercer paso de la creación de una BaseDatosContacto.

        Este método se encarga de generar los objectos Contacto por cada linea
        del archivo de importación especificado para la base de datos de
        contactos.
        """
        pass

    def define_base_dato_contacto(self, base_datos_contacto):
        """
        Último paso de la creación de una BaseDatosContacto.

        Este método se encarga de marcar como definida y lista para su uso a
        la BaseDatosContacto.
        """
