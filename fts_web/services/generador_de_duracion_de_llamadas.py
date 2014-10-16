# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.db import connection
from django.db import transaction
from fts_daemon.models import EventoDeContacto
from fts_web.models import Campana, Contacto, DuracionDeLlamada
from fts_web.utiles import log_timing
import logging as _logging


logger = _logging.getLogger(__name__)


class GeneradorDeDuracionDeLlamandasService(object):
    """
    Genera los registros de DuracionDeLlamada para las llamdas realizadas en
    la campana.
    """

    def _drop_tablas_temporales_si_existen(self):

        cursor = connection.cursor()
        sql = """DROP TABLE IF EXISTS  fts_custom_cdr_temporal;
                 DROP TABLE IF EXISTS  fts_custom_edc_temporal"""

        with log_timing(logger, "_drop_tabla_temporal_si_existe tardo %s seg"):
            cursor.execute(sql)

    def _crear_tabla_temporal_desde_edc(self, campana):

        cursor = connection.cursor()
        sql = """CREATE TABLE fts_custom_edc_temporal AS SELECT
        campana_id, contacto_id, json_agg(evento) as eventos_del_contacto
        FROM fts_web_contacto INNER JOIN fts_daemon_eventodecontacto
        ON fts_web_contacto.id = fts_daemon_eventodecontacto.contacto_id
        WHERE campana_id = %(campana_id)s
        AND fts_daemon_eventodecontacto.evento IN (%(opcion_0)s, %(opcion_1)s,
            %(opcion_2)s, %(opcion_3)s, %(opcion_4)s, %(opcion_5)s,
            %(opcion_6)s, %(opcion_7)s, %(opcion_8)s, %(opcion_9)s)
        GROUP BY contacto_id, campana_id
        """
        params = {'campana_id': campana.id,
                  'opcion_0': EventoDeContacto.EVENTO_ASTERISK_OPCION_0,
                  'opcion_1': EventoDeContacto.EVENTO_ASTERISK_OPCION_1,
                  'opcion_2': EventoDeContacto.EVENTO_ASTERISK_OPCION_2,
                  'opcion_3': EventoDeContacto.EVENTO_ASTERISK_OPCION_3,
                  'opcion_4': EventoDeContacto.EVENTO_ASTERISK_OPCION_4,
                  'opcion_5': EventoDeContacto.EVENTO_ASTERISK_OPCION_5,
                  'opcion_6': EventoDeContacto.EVENTO_ASTERISK_OPCION_6,
                  'opcion_7': EventoDeContacto.EVENTO_ASTERISK_OPCION_7,
                  'opcion_8': EventoDeContacto.EVENTO_ASTERISK_OPCION_8,
                  'opcion_9': EventoDeContacto.EVENTO_ASTERISK_OPCION_9}

        with log_timing(logger,
                        "_crear_tabla_temporal_desde_edc() tardo %s seg"):
            cursor.execute(sql, params)

    def _crear_tabla_temporal_desde_cdr(self, campana):

        cursor = connection.cursor()
        sql = """CREATE TABLE fts_custom_cdr_temporal AS SELECT
        calldate as timestamp,
        CAST(substring(dcontext from '_(\d+)$') as integer) as campana_id,
        CAST(substring(dst from '(\d+)') as integer) as contacto_id,
        substring(dst from '-(\d+)-') as numero_telefono,
        duration as duracion_en_segundos
        FROM {0}
        WHERE dcontext = 'FTS_local_campana_%(campana_id)s'
        AND disposition IN ('ANSWERED')
        """.format(settings.FTS_NOMBRE_TABLA_CDR)

        params = {'campana_id': campana.id}

        with log_timing(logger,
                        "_crear_tabla_temporal_desde_cdr() tardo %s seg"):
            cursor.execute(sql, params)

    def _insertar_duracion_de_llamdas(self, campana):

        cursor = connection.cursor()
        sql = """INSERT INTO fts_web_duraciondellamada
        (fecha_hora_llamada, duracion_en_segundos, campana_id, numero_telefono,
         eventos_del_contacto)
        SELECT
        fts_custom_cdr_temporal.timestamp,
        fts_custom_cdr_temporal.duracion_en_segundos,
        fts_custom_cdr_temporal.campana_id,
        fts_custom_cdr_temporal.numero_telefono,
        fts_custom_edc_temporal.eventos_del_contacto
        FROM  fts_custom_edc_temporal
        INNER JOIN fts_custom_cdr_temporal ON
        fts_custom_edc_temporal.contacto_id =
        fts_custom_cdr_temporal.contacto_id
        WHERE fts_custom_edc_temporal.campana_id = %(campana_id)s
        """
        params = {'campana_id': campana.id, 'evento_iniciado':
                  EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO}

        with log_timing(logger,
                        "_insertar_duracion_de_llamdas() tardo %s seg"):
            cursor.execute(sql, params)

    def generar_duracion_de_llamdas_para_campana(self, campana):
        """
        Genera las DuracionDeLlamada para la campana. Es llamado desde el
        proceso de depuración de la campana.

        Supone que el cdr esta completo para la campana y existen todos los
        registros de las llamdas contestadas.
        """

        self._drop_tablas_temporales_si_existen()

        self._crear_tabla_temporal_desde_edc(campana)

        self._crear_tabla_temporal_desde_cdr(campana)

        self._insertar_duracion_de_llamdas(campana)
