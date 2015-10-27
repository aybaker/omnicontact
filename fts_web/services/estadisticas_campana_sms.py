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

    def obtener_estadisticas_reporte_sms_enviados(self, campana_sms):
        """
        Este método devuelve las estadísticas de
        la campaña actual.
        """
        assert campana_sms.estado in (CampanaSms.ESTADO_CONFIRMADA,
                                      CampanaSms.ESTADO_PAUSADA)

        servicio_estadisticas_sms = EstadisticasContactoReporteSms()
        datos_sms_enviados  = servicio_estadisticas_sms.\
            obtener_contacto_sms_enviado(campana_sms.id)
        lista_id = []
        lista_sms_enviado_fecha = []
        lista_destino = []
        lista_sms_enviado_estado = []
        lista_datos = []
        for dato in datos_sms_enviados:
            lista_id.append(dato[0])
            lista_sms_enviado_fecha.append(dato[1])
            lista_destino.append(dato[2])
            lista_sms_enviado_estado.append(FtsWebContactoSmsManager.\
                                            MAP_ESTADO_ENVIO_A_LABEL[dato[3]])
            lista_datos.append(dato[4])


        diccionario_sms_enviado = {
            'id': lista_id,
            'sms_enviado_fecha': lista_sms_enviado_fecha,
            'destino': lista_destino,
            'sms_enviado_estado': lista_sms_enviado_estado,
            'datos': lista_datos,
        }

        return diccionario_sms_enviado



