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
        contacto = {
            'id': None,
            'sms_enviado_fecha': None,
            'destino': None,
            'sms_enviado_estado': None,
            'datos': None,
        }
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



