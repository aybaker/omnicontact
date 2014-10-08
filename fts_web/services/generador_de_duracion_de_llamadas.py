# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import connection
from django.db import transaction
from fts_daemon.models import EventoDeContacto
from fts_web.models import Campana, Contacto, DuracionDeLlamada
import logging as _logging


logger = _logging.getLogger(__name__)


class GeneradorDeDuracionDeLlamandasService(object):
    """
    Genera los registros de DuracionDeLlamada para las llamdas realizadas en
    la campana.
    """

    def _validar_campana_estado_correcto(self, campana):
        """
        Valida que la campana se encuentre en el estado correcto. De lo
        contrario podrían no existir los registros de EventoDeContacto de esta
        campana y no se podría crear las DuracionDeLlamada.
        """

        # TODO: Implementar.

        return True

    def _obtener_eventos_de_contacto_de_campana(self, campana):
        """
        Devuelve los EventoDeContacto de la campana que tienen el evento:
        EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_ANSWER

        Supone que un contacto de una campana atiende una sola vez, por lo que
        habrá un registro por contacto que haya atendido.
        """

        eventos_de_contacto =  \
            EventoDeContacto.object.obtener_eventos_de_contacto_de_una_campana(
                campana.id)

    def _obtener_duracion_de_llamada(self, campana, contacto,
                                     numero_telefonico):
        """
        Devuelve la duración de la llamada obtenida de CDR que genera Asterisk.
        Se considera que esta configurado con la opción *unanswered en NO.
        Por lo que *supongo que debería haber un solo registro del contacto de
        la campana, simempre y cuádo la llamda haya sido atendida.

        *unanswered: Log unanswered calls. Normally, only answered calls result
        in a CDR. Logging all call attempts can result in a large number of
        extra call records that most people do not care about. The default
        value is no.
        """

        cursor = connection.cursor()
        sql = """SELECT duration FROM cdr
                  WHERE dcontext LIKE '%s-%s-%'
                  AND channel LIKE 'FTS_local_campana_%s'
                  AND disposition in ('ANSWERED')"""
        params = [contacto.id, numero_telefonico, campana.id]

        with log_timing(logger, "_obtener_duracion_de_llamada() tardo %s seg"):
            cursor.execute(sql, params)
            value = cursor.fetchone()
        return value[0]

    def generar_duracion_de_llamdas_para_campana(self, campana):
        """
        Genera las DuracionDeLlamada para la campana. Es llamado desde el
        proceso de depuración de la campana.
        Valida que la campana este en el estado correcto.
        Obtiene los eventos de contacto para las llamadas contestadas de la
        campana y por cada evento busca en cdr la duración de esa llamada que
        genero el evento de contacto.

        Supone que el cdr esta completo para la campana y existen todos los
        registros de las llamdas contestadas.
        """

        # Validamos la campana.
        self._validar_campana_estado_correcto(campana)

        # Obtenemos los eventos de contacto de la campana.
        eventos_de_contacto = self._obtener_eventos_de_contacto_de_campana(
            campana)

        for evento_de_contacto in eventos_de_contacto:
            contacto = Contacto.object.get(pk=evento_de_contacto.contacto_id)
            numero_telefonico, _ = contacto.obtener_telefono_y_datos_extras()

            duracion_en_segundos = self._obtener_duracion_de_llamada(
                campana.id, contacto.id, numero_telefonico)

            DuracionDeLlamada.objects.create(
                campana_id=evento_de_contacto.campana_id,
                numero_telefonico_contacto=numero_telefonico,
                fecha_hora_llamada=evento_de_contacto.timestamp,
                duracion_en_segundos=duracion_en_segundos)
