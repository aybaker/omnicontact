# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from fts_web.models import (BaseDatosContacto, Campana)
from fts_daemon.models import EventoDeContacto
from fts_web.errors import FtsRecicladoBaseDatosContactoError

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

    def _crear_base_datos(self, campana):
        bd_contacto = BaseDatosContacto.objects.create(
            nombre='{0} (reciclada)'.format(
                campana.bd_contacto.nombre),
            archivo_importacion=campana.bd_contacto.\
                archivo_importacion,
            nombre_archivo_importacion=campana.bd_contacto.\
                nombre_archivo_importacion,
        )
        return bd_contacto

    def reciclar(self, campana_id, tipos_reciclado):
        logger.info("Se iniciara el proceso de reciclado de base de datos"
                    " para la campana %s", campana_id)

        # Validamos que el parámetro tipos_reciclado contenga datos.
        if not tipos_reciclado:
            raise CampanaTipoRecicladoInvalidoError("No se selecciono un tipo "
                "de reciclado.")

        # Validamos que los datos de tipos_reciclado sean enteros.
        try:
            tipos_reciclado = [int(tipo_reciclado)
                               for tipo_reciclado in tipos_reciclado]
        except TypeError:
            raise CampanaTipoRecicladoInvalidoError("Ente los tipo de "
                    "reciclado seleccionados existe alguno que es invalido "
                    "para procesar el reciclado de contactos.")

        # Obtenemos la instancia de Campana que se esta reciclando y validamos
        # que se encuentre en el estado correcto.
        campana = self._obtener_campana(campana_id)
        if campana.estado != Campana.ESTADO_FINALIZADA:
            raise CampanaEstadoInvalidoError("El estado de la campana que "
                                             "se intenta reciclar no es: "
                                             "ESTADO_FINALIZADA.")

        if Campana.TIPO_RECICLADO_TOTAL in tipos_reciclado:
            # Validamos que si el tipo de reciclado es TIPO_RECICLADO_TOTAL,
            # sea el único tipo de reciclado que se procese.
            if len(tipos_reciclado) > 1:
                raise CampanaTipoRecicladoInvalidoError("Se seleccio mas de un"
                    " tipo de reciclado, cuando deberia ser solo el tipo:"
                    " TIPO_RECICLADO_TOTAL.")

            return campana.bd_contacto

        elif Campana.TIPO_RECICLADO_PENDIENTES in tipos_reciclado:
            # Validamos que si el tipo de reciclado es
            # TIPO_RECICLADO_PENDIENTES, sea el único tipo de reciclado que se
            # procese.
            if len(tipos_reciclado) > 1:
                raise CampanaTipoRecicladoInvalidoError("Se seleccio mas de un"
                    " tipo de reciclado, cuando deberia ser solo el tipo:"
                    " TIPO_RECICLADO_PENDIENTES.")

            contactos_reciclados =\
                EventoDeContacto.objects_reciclador_contactos.\
                obtener_contactos_reciclados(campana, tipos_reciclado)
        else:
            # Validamos que los tipos de reciclado correspondan con los tipos
            # de recicaldo posibles cuando se procesen mas de un tipo.
            if not all(tipo_reciclado in
                       dict(Campana.TIPO_RECICLADO_CONJUNTO)
                       for tipo_reciclado in tipos_reciclado):
                raise CampanaTipoRecicladoInvalidoError("Ente los tipo de "
                    "reciclado seleccionados existe alguno que es invalido "
                    "para procesar el reciclado de contactos.")

            contactos_reciclados =\
                EventoDeContacto.objects_reciclador_contactos.\
                obtener_contactos_reciclados(campana, tipos_reciclado)

        # Si no se devolvieron contactos reciclados se genera una excepción.
        if not contactos_reciclados:
            logger.warn("El reciclado de base datos no arrojo contactos.")
            raise FtsRecicladoBaseDatosContactoError("No se registraron "
                "contactos para reciclar con el tipo de reciclado "
                "seleccionado.")

        # Creamos la insancia de BaseDatosContacto para el reciclado.
        bd_contacto = self._crear_base_datos(campana)
        bd_contacto.genera_contactos(contactos_reciclados)
        bd_contacto.define()
        return bd_contacto
