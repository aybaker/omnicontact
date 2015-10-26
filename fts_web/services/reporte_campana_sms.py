# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import connection
from fts_web.models import CampanaSms
from fts_web.utiles import log_timing
import logging as _logging


logger = _logging.getLogger(__name__)


class EstadisticasContactoReporteSms():

    def obtener_contacto_sms_enviado(self, campana_sms_id):
        """
        Este método se encarga de devolver los contactos
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms_id))

        cursor = connection.cursor()
        sql = """SELECT id, sms_enviado_fecha, destino, sms_enviado, datos
            FROM  {0}
            WHERE campana_sms_id = %s
        """.format(nombre_tabla)

        params = [campana_sms_id]

        with log_timing(logger,
                        "obtener_contacto_sms_enviado() tardo %s seg"):
            cursor.execute(sql, params)
            values = cursor.fetchall()
            print values

        return values