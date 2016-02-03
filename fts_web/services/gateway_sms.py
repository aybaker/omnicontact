# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import connection
from fts_web.models import CampanaSms
from fts_web.utiles import log_timing
import codecs
import os
import json

import logging as _logging


logger = _logging.getLogger(__name__)

class GatewaySmsService(object):

    def crear_sms_en_el_servidor_ics(self, campana_sms):
        contactos_sin_procesar = self._obtener_contactos_no_procesados(
            campana_sms)
        for contacto in contactos_sin_procesar:
            contacto_json = json.loads(contacto[0])
            self._escribir_sms_en_send(contacto_json, 0,
                                       campana_sms.template_mensaje)

    def _obtener_contactos_no_procesados(self, campana_sms):
        """
        Este método se encarga de devolver los contactos no procesados
        El o significa no procesados en el codigo de daniel
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms.pk))

        cursor = connection.cursor()
        sql = """SELECT datos
            FROM  {0}
            WHERE sms_enviado = 0
            GROUP BY id, datos
        """.format(nombre_tabla)

        with log_timing(logger,
                        "_obtener_contactos_no_procesados() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        return values

    def _escribir_sms_en_send(self, numero, puerto, mensaje):

        dwgconfig_income_path = '/home/federico/FreeTech/gateway/'

        try:
            sms_partfilename = '%s%s' % (dwgconfig_income_path, numero)
            sms = codecs.open(sms_partfilename, 'w', 'utf-8')
            sms.write('%s\n' % numero)
            sms.write('%s\n' % puerto)
            sms.write('%s\n' % mensaje)

            sms.close()

        except:
            logger.error("error en la escritura del sms")
