# -*- coding: utf-8 -*-
"""
Modelos usados por el Daemon y el proxy AGI.


"""

from __future__ import unicode_literals

from django.db import connection
from fts_web.models import CampanaSms
from fts_web.utiles import log_timing
import logging as _logging


logger = _logging.getLogger(__name__)


class RecicladorContactosCampanaSMS():
    """
    Este manager se encarga de obtener los contactos según el tipo de
    reciclado de campana de sms que se realice.
    """

    def obtener_contactos_reciclados(self, campana_sms, tipos_reciclado):
        """
        Este método se encarga de iterar sobre los tipos de reciclado que
        se indiquen aplicar en el reciclado de campana. Según el tipo de
        reciclado se invoca al método adecuado para llevar a cabo la consulta
        correspondiente, y en caso de que sea mas de uno se sumarizan las
        mismas.
        """
        contactos_reciclados = set()
        for tipo_reciclado in tipos_reciclado:
            if int(tipo_reciclado) == CampanaSms.TIPO_RECICLADO_ERROR_ENVIO:
                contactos_reciclados.update(
                    self._obtener_contactos_error_envio(campana_sms))
            else:
                assert False, "El tipo de reciclado es invalido: {0}".format(
                    tipo_reciclado)
        return contactos_reciclados

    def _obtener_contactos_error_envio(self, campana_sms):
        """
        Este método se encarga de devolver los contactos que tengan el
        error en el envio de del sms
        El -1 significa error del envio en el codigo de daniel
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms.pk))

        cursor = connection.cursor()
        sql = """SELECT datos
            FROM  {0}
            WHERE sms_enviado = -1
            GROUP BY id, datos
        """.format(nombre_tabla)

        with log_timing(logger,
                        "_obtener_contactos_error_envio() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        return values
