# -*- coding: utf-8 -*-

"""
Servicio de activación de Campañas y Templates.
"""

from __future__ import unicode_literals

import logging

from fts_web.errors import FtsError

logger = logging.getLogger(__name__)


class ValidarCampanaError(FtsError):
    """Indica que no se puede activar la Campana/Template"""
    pass


class RestablecerDialplanError(FtsError):
    """Indica que se produjo un error al crear el dialplan."""
    pass


class ActivacionCampanaTemplateService(object):

    def _validar_campana(self, campana):
        """
        Valida que la campana tenga los atributos requeridos e indispensables
        para poder ser procesada.
        """

        if campana.bd_contacto.verifica_depurada():
            raise(ValidarCampanaError(
                "La Base de Datos de Contacto fue depurada en el proceso de "
                "creacion de la campana. No se pudo confirmar la creacion de "
                "de la campana."))

        if not campana.valida_tts():
            raise(ValidarCampanaError(
                "Las columnas de la base de datos seleccionado en el "
                "proceso de creacion de la campana no coinciden con los "
                "tts creado en audios de campana. Debe seleccionar una "
                "una base de datos valida."))

        if not campana.valida_grupo_atencion():
            raise(ValidarCampanaError(
                "EL Grupo Atención seleccionado en el proceso de creacion "
                "de la campana ha sido eliminado. Debe seleccionar uno "
                "valido."))

        if not campana.valida_derivacion_externa():
            raise(ValidarCampanaError(
                "La Derivacion Externa seleccionado en el proceso de "
                "creacion de la campana ha sido eliminada. Debe "
                "seleccionar uno valido."))

    def _restablecer_dialplan_campana(self):
        try:
            create_dialplan_config_file()
        except:
            logger.exception("ActivacionCampanaTemplateService: error al "
                             "intentar create_dialplan_config_file()")

            raise(RestablecerDialplanError(
                "hubo un inconveniente al generar el Dialplan de "
                "Asterisk."))

        # try:
        #     # Esto es algo redundante! Para que re-crear los queues?
        #     # Total, esto lo hace GrupoDeAtencion!
        #     create_queue_config_file()
        # except:
        #     logger.exception("ActivacionCampanaTemplateService: error al "
        #                     "intentar create_queue_config_file()")
        #     dialplan_ok = False
        #     message += ' Atencion: hubo un inconveniente al generar\
        #         la configuracion de Asterisk (queues).'

        try:
            ret = reload_config()
            if ret != 0:
                raise(RestablecerDialplanError(
                    "hubo un inconveniente al intentar recargar la "
                    "configuracion de Asterisk."))
        except:
            logger.exception("ActivacionCampanaTemplateService: error al "
                             " intentar reload_config()")

            raise(RestablecerDialplanError(
                "hubo un inconveniente al intentar recargar la "
                "configuracion de Asterisk."))

    def activar(self, campana):
        self._validar_campana(campana)
        campana.activar()
        if not campana.es_template:
            self._restablecer_dialplan_campana()
