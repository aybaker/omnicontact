# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from fts_web.models import CampanaSms
from fts_web.utiles import log_timing
from fts_web.services.datos_sms import EstadisticasContactoReporteSms,\
    FtsWebContactoSmsManager

import logging as _logging


logger = _logging.getLogger(__name__)


class EstadisticasCampanaSmsService():
    """
    Reporteria de las campaña sms
    """

    def obtener_estadisticas_reporte_sms_enviados(self, campana_sms_id):
        """
        Este método devuelve las estadísticas de
        la campaña actual.
        """

        campana_sms = CampanaSms.objects.get(pk=campana_sms_id)

        assert campana_sms.estado in (CampanaSms.ESTADO_CONFIRMADA,
                                      CampanaSms.ESTADO_PAUSADA)

        servicio_estadisticas_sms = EstadisticasContactoReporteSms()
        datos_sms_enviados  = servicio_estadisticas_sms.\
            obtener_contacto_sms_enviado(campana_sms.id)
        lista_contactos = []
        for dato in datos_sms_enviados:
            contacto = {
                'id': dato[0],
                'sms_enviado_fecha': dato[1],
                'destino': dato[2],
                'sms_enviado_estado': FtsWebContactoSmsManager.\
                    MAP_ESTADO_ENVIO_A_LABEL[dato[3]],
                'datos': dato[4],
            }
            lista_contactos.append(contacto)

        return lista_contactos

    def obtener_estadisticas_reporte_sms_recibido_respuesta(self,
                                                            campana_sms_id):
        """
        Este método devuelve las estadísticas de
        la campaña actual, un listado de los contactos que respondieron
        la repuesta esperada.
        """

        campana_sms = CampanaSms.objects.get(pk=campana_sms_id)

        assert campana_sms.estado in (CampanaSms.ESTADO_CONFIRMADA,
                                      CampanaSms.ESTADO_PAUSADA)
        assert campana_sms.tiene_respuesta

        servicio_estadisticas_sms = EstadisticasContactoReporteSms()
        datos_sms_recibido  = servicio_estadisticas_sms.\
            obtener_contacto_sms_repuesta_esperada(campana_sms.id)
        lista_contactos = []
        for dato in datos_sms_recibido:
            contacto = {
                'id_contacto': dato[0],
                'numero_contacto': dato[1],
                'fecha_envio': dato[2],
                'fecha_recibido': dato[3],
                'mensaje_respuesta': dato[4],
            }
            lista_contactos.append(contacto)

        return lista_contactos

    def obtener_estadisticas_reporte_sms_recibido_respuesta_invalida(self,
        campana_sms_id):
        """
        Este método devuelve las estadísticas de
        la campaña actual, un listado de los contactos que respondieron
        la repuesta esperada.
        """

        campana_sms = CampanaSms.objects.get(pk=campana_sms_id)

        assert campana_sms.estado in (CampanaSms.ESTADO_CONFIRMADA,
                                      CampanaSms.ESTADO_PAUSADA)
        assert campana_sms.tiene_respuesta

        servicio_estadisticas_sms = EstadisticasContactoReporteSms()
        datos_sms_recibido  = servicio_estadisticas_sms.\
            obtener_contacto_sms_repuesta_invalida(campana_sms.id)
        lista_contactos = []
        for dato in datos_sms_recibido:
            contacto = {
                'id_contacto': dato[0],
                'numero_contacto': dato[1],
                'fecha_envio': dato[2],
                'fecha_recibido': dato[3],
                'mensaje_respuesta': dato[4],
            }
            lista_contactos.append(contacto)

        return lista_contactos

    def _obtener_totales_por_estado_sms(self, lista_totales_estados):
        """
        Este se metodo se encarga de devolver los totales por estado de sms
        no procesado, error_envio y enviado
        """
        total_estado = {
            'total_enviado': 0,
            'total_error_envio': 0,
            'total_no_procesados': 0,
            'total_sin_confirmacion': 0,
        }

        for estado in lista_totales_estados:
            if estado[0] is FtsWebContactoSmsManager.ESTADO_ENVIO_ENVIADO:
                total_estado['total_enviado'] = estado[1]
            elif estado[0] is FtsWebContactoSmsManager.ESTADO_ENVIO_ERROR_ENVIO:
                total_estado['total_error_envio'] = estado[1]
            elif estado[0] is FtsWebContactoSmsManager.ESTADO_ENVIO_NO_PROCESADO:
                total_estado['total_no_procesados'] = estado[1]
            elif estado[0] is FtsWebContactoSmsManager.ESTADO_ENVIO_SIN_CONFIRMACION:
                total_estado['total_sin_confirmacion'] = estado[1]

        return total_estado

    def obtener_estadisticas_supervision(self, campana_sms_id):
        """
        Este metodo devuelve las estadisticas de la campaña sms
        """

        campana_sms = CampanaSms.objects.get(pk=campana_sms_id)

        assert campana_sms.estado in (CampanaSms.ESTADO_CONFIRMADA,
                                      CampanaSms.ESTADO_PAUSADA)

        servicio_estadisticas_sms = EstadisticasContactoReporteSms()
        lista_total_estado = servicio_estadisticas_sms.obtener_count_contactos_estado(campana_sms_id)
        total_estado_enviado = self._obtener_totales_por_estado_sms(lista_total_estado)
        total_recibidos_respuesta = servicio_estadisticas_sms.obtener_total_contacto_sms_repuesta_esperada(campana_sms_id)
        total_recibidos_respuesta_invalida = servicio_estadisticas_sms.\
            obtener_total_contacto_sms_repuesta_invalida(campana_sms_id)

        total_supervision = {
            'total_enviado': total_estado_enviado['total_enviado'],
            'total_error_envio': total_estado_enviado['total_error_envio'],
            'total_no_procesados': total_estado_enviado['total_no_procesados'],
            'total_recibidos_respuesta': total_recibidos_respuesta[0][0],
            'total_recibidos_respuesta_invalida': total_recibidos_respuesta_invalida[0][0],
        }

        return total_supervision

