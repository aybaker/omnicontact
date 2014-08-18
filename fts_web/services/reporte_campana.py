# -*- coding: utf-8 -*-

"""
Servicio de reportes de campanas
"""

from __future__ import unicode_literals

import csv
import logging
import os

from django.conf import settings
from fts_web.models import Campana
from fts_web.utiles import crear_archivo_en_media_root


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

        dirname, filename = crear_archivo_en_media_root(dirname,
            "{0}-reporte".format(campana.id), ".csv")

        values = EventoDeContacto.objects_estadisticas\
            .obtener_opciones_por_contacto(campana.pk)

        with open(file_path, 'wb') as csvfile:
            # Creamos encabezado
            encabezado = ["nro_telefono"]
            opciones_dict = dict([(op.digito, op.get_descripcion_de_opcion())
                for op in campana.opciones.all()])
            for opcion in range(10):
                try:
                    encabezado.append(opciones_dict[opcion])
                except KeyError:
                    encabezado.append("#{0} - Opcion invalida".format(opcion))

            # Creamos csvwriter y guardamos encabezado y luego datos
            csvwiter = csv.writer(csvfile)
            csvwiter.writerow(encabezado)
            for telefono, lista_eventos in values:
                lista_opciones = [telefono]
                for opcion in range(10):
                    evento = EventoDeContacto.NUMERO_OPCION_MAP[opcion]
                    if evento in lista_eventos:
                        lista_opciones.append(1)
                    else:
                        lista_opciones.append(None)
                csvwiter.writerow(lista_opciones)
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
