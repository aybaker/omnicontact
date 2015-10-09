# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from fts_web.models import (BaseDatosContacto, Campana, CampanaSms)
from fts_daemon.models import EventoDeContacto
from fts_web.errors import FtsRecicladoBaseDatosContactoError
from fts_web.reciclador_base_datos_contacto.reciclado_de_contacto_sms import \
    RecicladorContactosCampanaSMS

import logging as _logging

logger = _logging.getLogger(__name__)


class CampanaEstadoInvalidoError(FtsRecicladoBaseDatosContactoError):
    pass


class CampanaTipoRecicladoInvalidoError(FtsRecicladoBaseDatosContactoError):
    pass


class RecicladorBaseDatosContacto(object):
    """
    Este objeto se encarga de llevar a cabo el reciclado de los contactos de
    una Campana, según el o los tipos de reciclados que se quieran aplicar.
    Devuelve la instancia de BaseDatosContacto que se usará en la campana
    reciclada.
    """

    def _obtener_campana(self, campana_id):
        return Campana.objects.get(pk=campana_id)

    def _obtener_campana_sms(self, campana_id):
        return CampanaSms.objects.get(pk=campana_id)

    def reciclar(self, campana_id, tipos_reciclado):
        logger.info("Se iniciara el proceso de reciclado de base de datos"
                    " para la campana %s", campana_id)

        # Validamos que el parámetro tipos_reciclado contenga datos.
        if not tipos_reciclado:
            raise CampanaTipoRecicladoInvalidoError(
                "No se selecciono un tipo de reciclado.")

        # Validamos que los datos de tipos_reciclado sean enteros.
        try:
            tipos_reciclado = [int(tipo_reciclado)
                               for tipo_reciclado in tipos_reciclado]
        except TypeError:
            raise CampanaTipoRecicladoInvalidoError(
                "Ente los tipo de reciclado seleccionados existe alguno que "
                "es invalido para procesar el reciclado de contactos.")

        # Obtenemos la instancia de Campana que se esta reciclando y validamos
        # que se encuentre en el estado correcto.
        campana = self._obtener_campana(campana_id)
        if campana.estado != Campana.ESTADO_DEPURADA:
            raise CampanaEstadoInvalidoError(
                "El estado de la campana que se intenta reciclar no es: "
                "ESTADO_DEPURADA.")

        if Campana.TIPO_RECICLADO_TOTAL in tipos_reciclado:
            # Validamos que si el tipo de reciclado es TIPO_RECICLADO_TOTAL,
            # sea el único tipo de reciclado que se procese.
            if len(tipos_reciclado) > 1:
                raise CampanaTipoRecicladoInvalidoError(
                    "Se selecciono mas de un tipo de reciclado, cuando "
                    "deberia ser solo el tipo: TIPO_RECICLADO_TOTAL.")

            return campana.bd_contacto

        elif Campana.TIPO_RECICLADO_PENDIENTES in tipos_reciclado:
            # Validamos que si el tipo de reciclado es
            # TIPO_RECICLADO_PENDIENTES, sea el único tipo de reciclado que se
            # procese.
            if len(tipos_reciclado) > 1:
                raise CampanaTipoRecicladoInvalidoError(
                    "Se selecciono mas de un tipo de reciclado, cuando "
                    "deberia ser solo el tipo: TIPO_RECICLADO_PENDIENTES.")

            contactos_reciclados =\
                EventoDeContacto.objects_reciclador_contactos.\
                obtener_contactos_reciclados(campana, tipos_reciclado)
        else:
            # Validamos que los tipos de reciclado correspondan con los tipos
            # de recicaldo posibles cuando se procesen mas de un tipo.
            if not all(tipo_reciclado in
                       dict(Campana.TIPO_RECICLADO_CONJUNTO)
                       for tipo_reciclado in tipos_reciclado):
                raise CampanaTipoRecicladoInvalidoError(
                    "Ente los tipo de reciclado seleccionados existe alguno "
                    "que es invalido para procesar el reciclado de contactos.")

            contactos_reciclados =\
                EventoDeContacto.objects_reciclador_contactos.\
                obtener_contactos_reciclados(campana, tipos_reciclado)

        # Si no se devolvieron contactos reciclados se genera una excepción.
        if not contactos_reciclados:
            logger.warn("El reciclado de base datos no arrojo contactos.")
            raise FtsRecicladoBaseDatosContactoError(
                "No se registraron contactos para reciclar con el tipo de "
                "reciclado seleccionado.")

        # Creamos la insancia de BaseDatosContacto para el reciclado.
        bd_contacto_reciclada = campana.bd_contacto.copia_para_reciclar()
        bd_contacto_reciclada.genera_contactos(contactos_reciclados)
        bd_contacto_reciclada.define()
        return bd_contacto_reciclada

    def reciclar_campana_sms(self, campana_sms_id, tipos_reciclado):
        logger.info("Se iniciara el proceso de reciclado de base de datos"
                    " para la campana de sms %s", campana_sms_id)

        # Validamos que el parámetro tipos_reciclado contenga datos.
        if not tipos_reciclado:
            raise CampanaTipoRecicladoInvalidoError(
                "No se selecciono un tipo de reciclado.")

        # Validamos que los datos de tipos_reciclado sean enteros.
        try:
            tipos_reciclado = [int(tipo_reciclado)
                               for tipo_reciclado in tipos_reciclado]
        except TypeError:
            raise CampanaTipoRecicladoInvalidoError(
                "Ente los tipo de reciclado seleccionados existe alguno que "
                "es invalido para procesar el reciclado de contactos.")

        # Obtenemos la instancia de CampanaSms que se esta reciclando y
        # validamos que se encuentre en el estado correcto.
        campana_sms = self._obtener_campana_sms(campana_sms_id)
        if campana_sms.estado not in (CampanaSms.ESTADO_CONFIRMADA,
                                  CampanaSms.ESTADO_PAUSADA):
            raise CampanaEstadoInvalidoError(
                "El estado de la campana que se intenta reciclar no es: "
                "ESTADO_CONFIRMADA ó ESTADO_PAUSADA.")

        if CampanaSms.TIPO_RECICLADO_TOTAL in tipos_reciclado:
            # Validamos que si el tipo de reciclado es TIPO_RECICLADO_TOTAL,
            # sea el único tipo de reciclado que se procese.
            if len(tipos_reciclado) > 1:
                raise CampanaTipoRecicladoInvalidoError(
                    "Se selecciono mas de un tipo de reciclado, cuando "
                    "deberia ser solo el tipo: TIPO_RECICLADO_TOTAL.")

            return campana_sms.bd_contacto

        elif CampanaSms.TIPO_RECICLADO_ERROR_ENVIO in tipos_reciclado:
            # Validamos que si el tipo de reciclado es
            # TIPO_RECICLADO_PENDIENTES, sea el único tipo de reciclado que se
            # procese.
            if len(tipos_reciclado) > 1:
                raise CampanaTipoRecicladoInvalidoError(
                    "Se selecciono mas de un tipo de reciclado, cuando "
                    "deberia ser solo el tipo: TIPO_RECICLADO_ERROR_ENVIO.")
            reciclador = RecicladorContactosCampanaSMS()
            contactos_reciclados = reciclador.\
                obtener_contactos_reciclados(campana_sms, tipos_reciclado)

            # Si no se devolvieron contactos reciclados se genera una excepción.
            if not contactos_reciclados:
                logger.warn("El reciclado de base datos no arrojo contactos.")
                raise FtsRecicladoBaseDatosContactoError(
                    "No se registraron contactos para reciclar con el tipo de "
                    "reciclado seleccionado.")

            # Creamos la insancia de BaseDatosContacto para el reciclado.
            bd_contacto_reciclada = campana_sms.bd_contacto.copia_para_reciclar()
            bd_contacto_reciclada.genera_contactos(contactos_reciclados)
            bd_contacto_reciclada.define()
            return bd_contacto_reciclada

        else:
            raise CampanaTipoRecicladoInvalidoError(
                    "No se selecciono un tipo de reciclado valido ")