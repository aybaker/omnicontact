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
from fts_web.models import Campana
from fts_web.utiles import crear_archivo_en_media_root
from django.utils.encoding import force_text


logger = logging.getLogger(__name__)


class ReporteCampanaService(object):

    def crea_reporte_csv(self, campana):
        from fts_daemon.models import EventoDeContacto

        assert campana.estado == Campana.ESTADO_FINALIZADA

        dirname = 'reporte_campana'
        filename = "{0}-reporte.csv".format(campana.id)
        file_path = os.path.join(settings.MEDIA_ROOT, dirname, filename)

        file_url = "{0}{1}/{2}".format(settings.MEDIA_URL, dirname, filename)

        if os.path.exists(file_path):
            # Esto no debería suceder.
            logger.warn("crea_reporte_csv(): Ya existe archivo CSV de "
                        "reporte para la campana %s. Archivo: %s. "
                        "El archivo sera sobreescrito", campana.pk, file_path)

        dirname, filename = crear_archivo_en_media_root(
            dirname, "{0}-reporte".format(campana.id), ".csv")

        contacto_opciones = EventoDeContacto.objects_estadisticas\
            .obtener_opciones_por_contacto(campana.pk)

        with open(file_path, 'wb') as csvfile:
            # Creamos encabezado
            encabezado = []

            cantidad_datos = len(json.loads(contacto_opciones[0][0]))
            for c in range(cantidad_datos):
                encabezado.append("Extra{0}".format(c+1))

            opciones_dict = dict([(op.digito, op.get_descripcion_de_opcion())
                                 for op in campana.opciones.all()])

            for opcion in range(10):
                try:
                    encabezado.append(opciones_dict[opcion])
                except KeyError:
                    encabezado.append(u"#{0} - N/A".format(opcion))

            # Creamos csvwriter
            csvwiter = csv.writer(csvfile)

            # guardamos encabezado
            lista_encabezados_utf8 = [force_text(item).encode('utf-8')
                                      for item in encabezado]
            csvwiter.writerow(lista_encabezados_utf8)

            # guardamos datos
            for contacto, lista_eventos in contacto_opciones:
                lista_opciones = []
                for dato in json.loads(contacto):
                    lista_opciones.append(dato)

                for opcion in range(10):
                    evento = EventoDeContacto.NUMERO_OPCION_MAP[opcion]
                    if evento in lista_eventos:
                        lista_opciones.append(1)
                    else:
                        lista_opciones.append(None)

                lista_opciones_utf8 = [force_text(item).encode('utf-8')
                                       for item in lista_opciones]
                csvwiter.writerow(lista_opciones_utf8)

        return file_url

    def obtener_url_reporte_csv_descargar(self, campana):
        assert campana.estado == Campana.ESTADO_DEPURADA

        dirname = 'reporte_campana'
        filename = "{0}-reporte.csv".format(campana.id)
        file_path = "{0}/{1}/{2}".format(settings.MEDIA_ROOT, dirname,
                                         filename)
        file_url = "{0}{1}/{2}".format(settings.MEDIA_URL, dirname,
                                        filename)
        if os.path.exists(file_path):
            return file_url

        # Esto no debería suceder.
        logger.error("obtener_url_reporte_csv_descargar(): NO existe archivo"
                     " CSV de descarga para la campana %s", campana.pk)
        assert os.path.exists(file_path)
