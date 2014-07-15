# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from fts_web.models import (BaseDatosContacto, Campana)
from fts_web.errors import FtsRecicladoBaseDatosContactoError

import logging as _logging

logger = _logging.getLogger(__name__)


class RecicladorBaseDatosContacto(object):
    def _obtener_campana(self, campana_id):
        return Campana.objects.get(pk=campana_id)

    def _obtener_contactos_reciclados(self, campana, tipo_reciclado):
        # CODE SMELL: el metodo devuelve 2 tipos de datos diferentes

        if int(tipo_reciclado) == Campana.TIPO_RECICLADO_TOTAL:
            contactos_reciclados = campana.bd_contacto
        elif int(tipo_reciclado) == Campana.TIPO_RECICLADO_PENDIENTES:
            contactos_reciclados = campana.obtener_contactos_pendientes()

        elif int(tipo_reciclado) == Campana.TIPO_RECICLADO_OCUPADOS:
            contactos_reciclados = campana.obtener_contactos_ocupados()
        elif int(tipo_reciclado) == Campana.TIPO_RECICLADO_NO_CONTESTADOS:
            contactos_reciclados = \
                campana.obtener_contactos_no_contestados()
        elif int(tipo_reciclado) == Campana.TIPO_RECICLADO_NUMERO_ERRONEO:
            contactos_reciclados = \
                campana.obtener_contactos_numero_erroneo()
        elif int(tipo_reciclado) == Campana.TIPO_RECICLADO_LLAMADA_ERRONEA:
            contactos_reciclados = \
                campana.obtener_contactos_llamada_erronea()
        else:
            return None
        return contactos_reciclados

    def reciclar(self, campana_id, tipo_reciclado):
        logger.info("Se iniciara el proceso de reciclado de base de datos"
                    " para la campana %s", campana_id)
        campana = self._obtener_campana(campana_id)

        contactos_reciclados = self._obtener_contactos_reciclados(campana,
            tipo_reciclado)

        if not contactos_reciclados:
            logger.warn("El reciclado de base datos no arrojo contactos.")
            # CODE SMELL: mensajes de log / de excepcion con multiples lineas
            raise FtsRecicladoBaseDatosContactoError("""No se registraron
                contactos para reciclar con el tipo de reciclado seleccionado
                .""")

        if isinstance(contactos_reciclados, BaseDatosContacto):
            return contactos_reciclados

        # CODE SMELL: se maneja la excepción, pero no se recupera del error!
        # Seguramente es mejor NO manejar la excepcion, y que quien llame
        # a este metodo se encargue de manejarla.
        try:
            bd_contacto = BaseDatosContacto.objects.create(
                nombre='{0} (reciclada)'.format(
                    campana.bd_contacto.nombre),
                archivo_importacion=campana.bd_contacto.\
                    archivo_importacion,
                nombre_archivo_importacion=campana.bd_contacto.\
                    nombre_archivo_importacion,
            )
        except Exception, e:
            # CODE SMELL: excep de Exception (y no de un tipo específico)
            # CODE SMELL: no se loguea traceback
            logger.warn("Se produjo un error al intentar crear la base de"
                " datos. Exception: %s", e)
            # FIXME: se encapsula una excepcion generica (Exception), o sea,
            # un error generado por OTRO componente (no por el Reciclador)
            # en una excepción del reciclador. Las excepciones del Reciclador
            # deberian indicar un problema en el reciclado en sí.
            # CODE SMELL: mensajes de log / de excepcion con multiples lineas
            raise FtsRecicladoBaseDatosContactoError("""No se pudo crear
                la base datos contactos reciclada.""")
        else:
            bd_contacto.genera_contactos(contactos_reciclados)
            bd_contacto.define()
            return bd_contacto
