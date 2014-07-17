# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from fts_web.models import (BaseDatosContacto, Campana)
from fts_daemon.models import EventoDeContacto
from fts_web.errors import FtsRecicladoBaseDatosContactoError

import logging as _logging

logger = _logging.getLogger(__name__)


class RecicladorBaseDatosContacto(object):
    def _obtener_campana(self, campana_id):
        return Campana.objects.get(pk=campana_id)

    def reciclar(self, campana_id, tipos_reciclado):
        logger.info("Se iniciara el proceso de reciclado de base de datos"
                    " para la campana %s", campana_id)

        campana = self._obtener_campana(campana_id)

        if int(tipos_reciclado[0]) == Campana.TIPO_RECICLADO_TOTAL:
            return campana.bd_contacto
        else:
            contactos_reciclados =\
                EventoDeContacto.objects_reciclador_contactos.\
                obtener_contactos_reciclados(campana, tipos_reciclado)

            if not contactos_reciclados:
                logger.warn("El reciclado de base datos no arrojo contactos.")
                raise FtsRecicladoBaseDatosContactoError("No se registraron "
                    "contactos para reciclar con el tipo de reciclado "
                    "seleccionado.")

            bd_contacto = BaseDatosContacto.objects.create(
                nombre='{0} (reciclada)'.format(
                    campana.bd_contacto.nombre),
                archivo_importacion=campana.bd_contacto.\
                    archivo_importacion,
                nombre_archivo_importacion=campana.bd_contacto.\
                    nombre_archivo_importacion,
            )
            bd_contacto.genera_contactos(contactos_reciclados)
            bd_contacto.define()
            return bd_contacto
