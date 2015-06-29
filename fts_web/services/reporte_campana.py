# -*- coding: utf-8 -*-

"""
Servicio de reportes de campanas
"""

from __future__ import unicode_literals

import csv
import logging
import os
import json

from django.conf import settings
from fts_web.models import Campana, Contacto
from fts_web.utiles import crear_archivo_en_media_root

from fts_daemon.models import EventoDeContacto

from django.utils.encoding import force_text


logger = logging.getLogger(__name__)


class ArchivoDeReporteCsv(object):
    def __init__(self, campana):
        self._campana = campana
        self.nombre_del_directorio = 'reporte_campana'
        self.prefijo_nombre_de_archivo = "{0}-reporte".format(self._campana.id)
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
                        "reporte para la campana %s. Archivo: %s. "
                        "El archivo sera sobreescrito", self._campana.pk,
                        self.ruta)

        crear_archivo_en_media_root(
            self.nombre_del_directorio,
            self.prefijo_nombre_de_archivo,
            self.sufijo_nombre_de_archivo)

    def escribir_archivo_csv(self, opciones_por_contacto):
        finalizadores = EventoDeContacto.objects.get_eventos_finalizadores()
        with open(self.ruta, 'wb') as csvfile:
            # Creamos encabezado
            encabezado = []

            cantidad_datos = len(json.loads(opciones_por_contacto[0][0]))
            for c in range(cantidad_datos):
                encabezado.append("Extra{0}".format(c+1))

            encabezado.append("Fecha de la llamada")

            opciones_dict = dict([(op.digito, op.get_descripcion_de_opcion())
                                 for op in self._campana.opciones.all()])

            for opcion in range(10):
                try:
                    encabezado.append(opciones_dict[opcion])
                except KeyError:
                    encabezado.append(u"#{0} - N/A".format(opcion))

            encabezado.append("Contesto: Humano")
            encabezado.append("Contesto: Maquina")
            encabezado.append("Contesto: Indefinido")
            encabezado.append("No contesto")
            encabezado.append("Ocupado")
            encabezado.append("Canal no disponible")
            encabezado.append("Congestion")
            # Creamos csvwriter
            csvwiter = csv.writer(csvfile)

            # guardamos encabezado
            lista_encabezados_utf8 = [force_text(item).encode('utf-8')
                                      for item in encabezado]
            csvwiter.writerow(lista_encabezados_utf8)

            # guardamos datos
            for contacto, lista_eventos, lista_tiempo in opciones_por_contacto:
                lista_opciones = []

                for dato in json.loads(contacto):
                    lista_opciones.append(dato)

#                lista_opciones.append(None)

                for opcion in range(10):
                    evento = EventoDeContacto.NUMERO_OPCION_MAP[opcion]
                    if evento in lista_eventos:
                        lista_opciones.append(1)
                    else:
                        lista_opciones.append(None)

                if EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED in lista_eventos:
                    lista_opciones.append(1)
                else:
                    lista_opciones.append(None)

                if EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED in lista_eventos:
                    lista_opciones.append(1)
                else:
                    lista_opciones.append(None)

                if EventoDeContacto.EVENTO_ASTERISK_AMD_FAILED in lista_eventos:
                    lista_opciones.append(1)
                else:
                    lista_opciones.append(None)

                indice_evento = 0
                finalizado = False
                for finalizador in finalizadores:
                    if finalizador in lista_eventos:
                        finalizado = True
                        indice_evento = lista_eventos.index(finalizador)
                        break
                if finalizado:

                    tiempo_llamada = lista_tiempo[indice_evento]
                    lista_opciones.insert(cantidad_datos, tiempo_llamada)
                    # opciones de no contestados
                    lista_opciones.append(None)
                    lista_opciones.append(None)
                    lista_opciones.append(None)
                    lista_opciones.append(None)
                
                else:

                    # aca se guarda el evento priorida priorizando siempre a busy
                    # Este es el orden de prioridad busy, no answer,failed
                    # (congestion, canal no disponible)
                    evento_prioridad = 0
                    for ev in lista_eventos:

                        if ev is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY:
                            evento_prioridad = ev
                            indice_evento = lista_eventos.index(ev)
                            break
                        elif ev is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER:
                            evento_prioridad = ev
                            indice_evento = lista_eventos.index(ev)
                        elif ev is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL or\
                        ev is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION:
                            if not evento_prioridad is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER:
                                evento_prioridad = ev
                                indice_evento = lista_eventos.index(ev)

                    if evento_prioridad != 0:

                        if evento_prioridad is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER:
                            lista_opciones.append(1)
                        elif evento_prioridad is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY:
                            lista_opciones.append(1)
                        elif evento_prioridad is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL:
                            lista_opciones.append(1)
                        elif evento_prioridad is EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION:
                            lista_opciones.append(1)

                        tiempo_llamada = lista_tiempo[indice_evento]
                        lista_opciones.insert(cantidad_datos, tiempo_llamada)


                lista_opciones_utf8 = [force_text(item).encode('utf-8')
                                       for item in lista_opciones]
                csvwiter.writerow(lista_opciones_utf8)

    def ya_existe(self):
        return os.path.exists(self.ruta)


class ReporteCampanaService(object):

    def _obtener_opciones_por_contacto(self, campana):
        opciones_por_contacto = EventoDeContacto.objects_estadisticas\
            .obtener_opciones_por_contacto(campana.pk)
        return opciones_por_contacto

    def _obtener_fecha_hora_llamada_por_contacto(self, campana):
        fecha_hora_por_contacto = EventoDeContacto.objects_estadisticas.\
            obtener_fecha_hora_por_contacto(campana)
        return fecha_hora_por_contacto

    def crea_reporte_csv(self, campana):
        assert campana.estado == Campana.ESTADO_FINALIZADA

        archivo_de_reporte = ArchivoDeReporteCsv(campana)

        archivo_de_reporte.crear_archivo_en_directorio()

        opciones_por_contacto = self._obtener_opciones_por_contacto(campana)

        fecha_hora_por_contacto = self._obtener_fecha_hora_llamada_por_contacto(campana)

        archivo_de_reporte.escribir_archivo_csv(opciones_por_contacto)

    def obtener_url_reporte_csv_descargar(self, campana):
        assert campana.estado == Campana.ESTADO_DEPURADA

        archivo_de_reporte = ArchivoDeReporteCsv(campana)
        if archivo_de_reporte.ya_existe():
            return archivo_de_reporte.url_descarga

        # Esto no debería suceder.
        logger.error("obtener_url_reporte_csv_descargar(): NO existe archivo"
                     " CSV de descarga para la campana %s", campana.pk)
        assert os.path.exists(archivo_de_reporte.url_descarga)
