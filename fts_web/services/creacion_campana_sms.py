# -*- coding: utf-8 -*-

"""
Servicio de activación de Campañas y Templates.
"""

from __future__ import unicode_literals

import logging

from django.conf import settings
from fts_web.errors import FtsError
from fts_web.services.datos_sms import FtsWebContactoSmsManager
from fts_web.services.gateway_sms import GatewaySmsService

logger = logging.getLogger(__name__)


class ValidarCampanaSmsError(FtsError):
    """Indica que no se puede activar la Campana/Template"""
    pass


class ConfirmacionCampanaSmsService(object):

    def _validar_bd_contacto_campana(self, campana):
        if campana.bd_contacto.verifica_depurada():
            raise(ValidarCampanaSmsError(
                "La Base de Datos de Contacto fue depurada en el proceso de "
                "creacion de la campana. No se pudo confirmar la creacion de "
                "de la campana."))

    def _validar_actuacion_campana(self, campana):
        if not campana.valida_actuaciones():
            raise(ValidarCampanaSmsError(
                "Las Actuaciones de la campana no son validas. Debe "
                "seleccionar actuaciones validas."))

    def _validar_mensaje(self, campana):
        if not campana.valida_mensaje():
            raise(ValidarCampanaSmsError(
                "Debe ingresar el cuerpo de mensaje es obligatorio."))

    def _depurar_fts_web_contacto(self, campana_sms):
        """
        Crea la tabla fts_web_contacto_{0} para el demonio_sms
        """
        service_datos_sms = FtsWebContactoSmsManager()
        service_datos_sms.crear_tabla_de_fts_web_contacto(campana_sms.id)

    def _elegir_demonio_sms(self, campana_sms):
        """
        Escoge el demonio seteado en el setting
        :param campana_sms: campaña sms creada
        """
        if settings.FTS_SMS_UTILIZADO is 'gateway':
            service_gateway_sms = GatewaySmsService()
            service_gateway_sms.crear_sms_en_el_servidor_ics(campana_sms)

    def confirmar(self, campana_sms):
        self._validar_bd_contacto_campana(campana_sms)
        self._validar_actuacion_campana(campana_sms)
        self._validar_mensaje(campana_sms)
        self._depurar_fts_web_contacto(campana_sms)
        self._elegir_demonio_sms(campana_sms)

        campana_sms.confirmar()
