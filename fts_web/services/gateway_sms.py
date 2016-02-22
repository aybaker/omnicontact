# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import connection
from fts_web.models import CampanaSms
from fts_web.utiles import log_timing
import codecs
import os
import json
import random

import logging as _logging


logger = _logging.getLogger(__name__)

class GatewaySmsService(object):

    def crear_sms_en_el_servidor_ics(self, campana_sms):
        """
        En este metodo vamos buscar los sms a enviar y lo vamos a crear
        y escribir en el servidor
        """
        contactos_sin_procesar = self._obtener_contactos_no_procesados(
            campana_sms)

        for contacto in contactos_sin_procesar:

            contacto_json = json.loads(contacto[1])
            cont = 0
            nombres_columnas = campana_sms.bd_contacto.get_metadata().\
                nombres_de_columnas
            mensaje = self._random_mensajes(campana_sms.template_mensaje,
                campana_sms.template_mensaje_opcional,
                campana_sms.template_mensaje_alternativo)

            for columna in nombres_columnas:
                mensaje = mensaje.replace('$'+columna+'', contacto_json[cont])
                cont = cont + 1

            self._escribir_sms_en_send(contacto[0], contacto_json[0], 0,
                                       mensaje, campana_sms.id)

    def _obtener_contactos_no_procesados(self, campana_sms):
        """
        Este método se encarga de devolver los contactos no procesados
        El o significa no procesados en el codigo de daniel
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms.pk))

        cursor = connection.cursor()
        sql = """SELECT id, datos
            FROM  {0}
            WHERE sms_enviado = 0
            GROUP BY id, datos
        """.format(nombre_tabla)

        with log_timing(logger,
                        "_obtener_contactos_no_procesados() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        return values

    def _escribir_sms_en_send(self, id, numero, puerto, mensaje, campana_sms_id):
        """
        Este metodo escribir los archivos sms en el servidor
        """

        dwgconfig_income_path = '/home/federico/FreeTech/gateway/'

        try:
            sms_partfilename = '%s%s.%s' % (dwgconfig_income_path, id,
                                            campana_sms_id)

            sms = codecs.open(sms_partfilename, 'w', 'utf-8')
            sms.write('%s\n' % numero)
            sms.write('%s\n' % puerto)
            sms.write('%s\n' % mensaje)

            sms.close()

        except:
            logger.error("error en la escritura del sms")


    def _random_mensajes(self, mensaje_principal, mensaje_opcional, mensaje_alternativo):
        """ Este metodo hace un random entre los 3 tipos de mensajes si existe
        (opcional, alternativo) si no devuelve el mensaje_principal
        :return: devuelve el mensaje a enviar
        """
        if mensaje_principal and mensaje_opcional and mensaje_alternativo:
            mensajes = (mensaje_principal, mensaje_opcional, mensaje_alternativo)
            mensaje = random.choice(mensajes)
            return mensaje
        elif mensaje_principal and mensaje_opcional:
            mensajes = (mensaje_principal, mensaje_opcional)
            mensaje = random.choice(mensajes)
            return mensaje
        elif mensaje_principal and  mensaje_alternativo:
            mensajes = (mensaje_principal, mensaje_alternativo)
            mensaje = random.choice(mensajes)
            return mensaje
        elif mensaje_principal:
            return mensaje_principal
        else:
            return None
