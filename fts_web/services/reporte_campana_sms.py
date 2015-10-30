# -*- coding: utf-8 -*-

"""
Servicio de reportes de campanas
"""

from __future__ import unicode_literals

import csv
import logging
import os
import json
import datetime
from pytz import timezone

from django.conf import settings
from fts_web.models import CampanaSms
from fts_web.utiles import crear_archivo_en_media_root

from django.utils.encoding import force_text


logger = logging.getLogger(__name__)

TIMEZONE_CONFIGURADA = timezone(settings.TIME_ZONE)


def convert_timestamp_fecha_hora_local(timestamp):
    """
    Este metodo convierte los timestamp, a fecha hora local
    """
    fecha_convertida = timestamp.astimezone(TIMEZONE_CONFIGURADA)
    return fecha_convertida


class ArchivoDeReporteCsv(object):
    def __init__(self, campana_sms):
        self._campana_sms = campana_sms
        self.nombre_del_directorio = 'reporte_campana_sms'
        self.prefijo_nombre_de_archivo = "{0}-reporte".format(self._campana_sms.id)
        self.sufijo_nombre_de_archivo = ".csv"
        self.nombre_de_archivo = "{0}{1}".format(
            self.prefijo_nombre_de_archivo, self.sufijo_nombre_de_archivo)
        self.url_descarga = os.path.join(settings.MEDIA_URL,
                                         self.nombre_del_directorio,
                                         self.nombre_de_archivo)
        self.ruta = os.path.join(settings.MEDIA_ROOT,
                                 self.nombre_del_directorio,
                                 self.nombre_de_archivo)

    def crear_archivo_en_directorio(self):
        if self.ya_existe():
            # Esto puede suceder si en un intento previo de depuracion, el
            # proceso es abortado, y por lo tanto, el archivo puede existir.
            logger.warn("ArchivoDeReporteCsv: Ya existe archivo CSV de "
                        "reporte para la campana_sms %s. Archivo: %s. "
                        "El archivo sera sobreescrito", self._campana_sms.pk,
                        self.ruta)

        crear_archivo_en_media_root(
            self.nombre_del_directorio,
            self.prefijo_nombre_de_archivo,
            self.sufijo_nombre_de_archivo)

    def escribir_archivo_csv_sms_enviados(self, contactos_enviados):

        with open(self.ruta, 'wb') as csvfile:
            # Creamos encabezado
            encabezado = []
            cantidad_datos = len(json.loads(contactos_enviados[0]['datos']))
            for c in range(cantidad_datos):
                encabezado.append("Extra{0}".format(c+1))
            encabezado.append("Id contacto")
            encabezado.append("Fecha de envio")
            encabezado.append("Destino")
            encabezado.append("Estado de envio")

            # Creamos csvwriter
            csvwiter = csv.writer(csvfile)

            # guardamos encabezado
            lista_encabezados_utf8 = [force_text(item).encode('utf-8')
                                      for item in encabezado]
            csvwiter.writerow(lista_encabezados_utf8)

            # Iteramos cada uno de los contactos, con los eventos de TODOS los intentos
            for contacto in contactos_enviados:
                lista_opciones = []
                for dato in json.loads(contacto['datos']):
                    lista_opciones.append(dato)
                lista_opciones.append(contacto['id'])
                lista_opciones.append(contacto['sms_enviado_fecha'])
                lista_opciones.append(contacto['destino'])
                lista_opciones.append(contacto['sms_enviado_estado'])

                # --- Finalmente, escribimos la linea

                lista_opciones_utf8 = [force_text(item).encode('utf-8')
                                       for item in lista_opciones]
                csvwiter.writerow(lista_opciones_utf8)

    def escribir_archivo_csv_sms_recibidos(self, contactos_enviados):

        with open(self.ruta, 'wb') as csvfile:
            # Creamos encabezado
            encabezado = []
            cantidad_datos = len(json.loads(contactos_enviados[0]['datos']))
            for c in range(cantidad_datos):
                encabezado.append("Extra{0}".format(c+1))
            encabezado.append("Id contacto")
            encabezado.append("Fecha de envio")
            encabezado.append("Destino")
            encabezado.append("Estado de envio")

            # Creamos csvwriter
            csvwiter = csv.writer(csvfile)

            # guardamos encabezado
            lista_encabezados_utf8 = [force_text(item).encode('utf-8')
                                      for item in encabezado]
            csvwiter.writerow(lista_encabezados_utf8)

            # Iteramos cada uno de los contactos, con los eventos de TODOS los intentos
            for contacto in contactos_enviados:
                lista_opciones = []
                for dato in json.loads(contacto['datos']):
                    lista_opciones.append(dato)
                lista_opciones.append(contacto['id'])
                lista_opciones.append(contacto['sms_enviado_fecha'])
                lista_opciones.append(contacto['destino'])
                lista_opciones.append(contacto['sms_enviado_estado'])

                # --- Finalmente, escribimos la linea

                lista_opciones_utf8 = [force_text(item).encode('utf-8')
                                       for item in lista_opciones]
                csvwiter.writerow(lista_opciones_utf8)

    def ya_existe(self):
        return os.path.exists(self.ruta)


class ReporteCampanaSmsService(object):

    REPORTE_SMS_ENVIADOS = "Reporte de SMS enviados"
    REPORTE_SMS_RECIBIDOS = "Reporte de SMS recibidos"

    def crea_reporte_csv(self, campana_sms, contactos, tipo_reporte):
        assert campana_sms.estado in (CampanaSms.ESTADO_CONFIRMADA,
                                      CampanaSms.ESTADO_PAUSADA)

        archivo_de_reporte = ArchivoDeReporteCsv(campana_sms)

        archivo_de_reporte.crear_archivo_en_directorio()

        if tipo_reporte is self.REPORTE_SMS_ENVIADOS:
            archivo_de_reporte.escribir_archivo_csv_sms_enviados(contactos)
        elif tipo_reporte is self.REPORTE_SMS_RECIBIDOS:
            archivo_de_reporte.escribir_archivo_csv_sms_recibidos(contactos)

    def obtener_url_reporte_csv_descargar(self, campana_sms):
        assert campana_sms.estado in (CampanaSms.ESTADO_CONFIRMADA,
                                      CampanaSms.ESTADO_PAUSADA)

        archivo_de_reporte = ArchivoDeReporteCsv(campana_sms)
        if archivo_de_reporte.ya_existe():
            return archivo_de_reporte.url_descarga

        # Esto no debería suceder.
        logger.error("obtener_url_reporte_csv_descargar(): NO existe archivo"
                     " CSV de descarga para la campana_sms %s", campana_sms.pk)
        assert os.path.exists(archivo_de_reporte.url_descarga)
