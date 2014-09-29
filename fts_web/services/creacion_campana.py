# -*- coding: utf-8 -*-

"""
Servicio de activación de Campañas y Templates.
"""

from __future__ import unicode_literals

import logging

from fts_web.errors import FtsError
from fts_daemon.asterisk_config import (DialplanConfigCreator,
                                        QueueConfigCreator,
                                        AsteriskConfigReloader)

logger = logging.getLogger(__name__)


class ValidarCampanaError(FtsError):
    """Indica que no se puede activar la Campana/Template"""
    pass


class RestablecerDialplanError(FtsError):
    """Indica que se produjo un error al crear el dialplan."""
    pass


class ActivacionCampanaTemplateService(object):

    def __init__(self):
        self.dialplan_config_creator = DialplanConfigCreator()
        self.queue_config_creator = QueueConfigCreator()
        self.reload_asterisk_config = AsteriskConfigReloader()

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

        if not campana.valida_audio():
            raise(ValidarCampanaError(
                "Los Audios de la campana no son validos. Debe seleccionar "
                "audios o tts validos."))

    def _validar_actuacion_campana(self, campana):
        if not campana.valida_actuaciones():
            raise(ValidarCampanaError(
                "Las Actuaciones de la campana no son validas. Debe "
                "seleccionar actuaciones validas."))

    def _generar_y_recargar_configuracion_asterisk(self):
        proceso_ok = True
        mensaje_error = ""

        try:
            self.dialplan_config_creator.create_config_file()
        except:
            logger.exception("ActivacionCampanaTemplateService: error al "
                             "intentar dialplan_config_creator()")

            proceso_ok = False
            mensaje_error += ("Hubo un inconveniente al crear el archivo de "
                              "configuracion del dialplan de Asterisk. ")
        try:
            # Esto es algo redundante! Para que re-crear los queues?
            # Total, esto lo hace GrupoDeAtencion!
            self.queue_config_creator.create_config_file()
        except:
            logger.exception("ActivacionCampanaTemplateService: error al "
                             "intentar queue_config_creator()")

            proceso_ok = False
            mensaje_error += ("Hubo un inconveniente al crear el archivo de "
                              "configuracion de colas de Asterisk. ")
        try:
            ret = self.reload_asterisk_config.reload_config()
            if ret != 0:
                proceso_ok = False
                mensaje_error += ("Hubo un inconveniente al intenar recargar "
                                  "la configuracion de Asterisk. ")
        except:
            logger.exception("ActivacionCampanaTemplateService: error al "
                             " intentar reload_config()")
            proceso_ok = False
            mensaje_error += ("Hubo un inconveniente al crear el archivo de "
                              "configuracion de colas de Asterisk. ")

        if not proceso_ok:
            raise(RestablecerDialplanError(mensaje_error))

    def activar(self, campana):
        self._validar_campana(campana)
        if campana.es_template:
            campana.activar_template()
        else:
            self._validar_actuacion_campana(campana)
            campana.activar()
            self._generar_y_recargar_configuracion_asterisk()
