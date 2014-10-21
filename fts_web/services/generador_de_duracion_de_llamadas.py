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

    def _drop_tabla_temporal_si_existe(self):
        """
        La tabla fts_custom_cdr_temporal se usa de manera temporal en la
        conformación de las DuracionDeLlamada para una campana.
        """

        cursor = connection.cursor()
        sql = """DROP TABLE IF EXISTS fts_custom_cdr_temporal"""

        with log_timing(logger, "_drop_tabla_temporal_si_existe tardo %s seg"):
            cursor.execute(sql)

    def _crear_tabla_temporal_desde_cdr(self, campana):
        """
        La tabla que se crea (fts_custom_cdr_temporal) reune los atributos
        necesarios de la tabla de CDR para luego poder combinarla con los
        registros de EventoDeContacto para una campana y conformar la
        DuracionDeLlamada para esa campana.
        """

        cursor = connection.cursor()
        sql = """CREATE TABLE fts_custom_cdr_temporal AS SELECT
        calldate as timestamp,
        CAST(substring(dcontext from '_(\d+)$') as integer) as campana_id,
        CAST(substring(dst from '(\d+)') as integer) as contacto_id,
        substring(dst from '-(\d+)-') as numero_telefono,
        billsec as duracion_en_segundos
        FROM {0}
        WHERE dcontext = 'FTS_local_campana_%(campana_id)s'
        AND disposition IN ('ANSWERED')
        """.format(settings.FTS_NOMBRE_TABLA_CDR)

        params = {'campana_id': campana.id}

        with log_timing(logger,
                        "_crear_tabla_temporal_desde_cdr() tardo %s seg"):
            cursor.execute(sql, params)

    def _insertar_duracion_de_llamdas(self, campana):
        """
        Realiza los inserciones en DuracionDeLlamada para una campana de los
        registros obtenidos de la combinación de EventoDeContacto y la tabla
        CDR.
        """
        cursor = connection.cursor()

        sql = """INSERT INTO fts_web_duraciondellamada
        (fecha_hora_llamada, duracion_en_segundos, campana_id, numero_telefono,
        eventos_del_contacto)
        SELECT
        fts_custom_cdr_temporal.timestamp,
        fts_custom_cdr_temporal.duracion_en_segundos,
        fts_custom_cdr_temporal.campana_id,
        fts_custom_cdr_temporal.numero_telefono,
        sub_query.eventos_del_contacto
        FROM fts_custom_cdr_temporal
        INNER JOIN
            (SELECT
            campana_id, contacto_id, json_agg(evento) AS eventos_del_contacto
            FROM fts_daemon_eventodecontacto
            WHERE campana_id = %(campana_id)s
            AND evento IN (%(opcion_0)s, %(opcion_1)s, %(opcion_2)s,
                           %(opcion_3)s, %(opcion_4)s, %(opcion_5)s,
                           %(opcion_6)s, %(opcion_7)s, %(opcion_8)s,
                           %(opcion_9)s)
            GROUP BY campana_id, contacto_id) AS sub_query
        ON fts_custom_cdr_temporal.contacto_id = sub_query.contacto_id
        WHERE fts_custom_cdr_temporal.campana_id = %(campana_id)s
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
                        "_insertar_duracion_de_llamdas() tardo %s seg"):
            cursor.execute(sql, params)

    def generar_duracion_de_llamdas_para_campana(self, campana):
        """
        Método público  llamado desde el proceso de depuración de la campana
        que se encarga de llamar a los métodos que realizan las consultas e
        inserciones necesarias para la creación de los registros de
        DuracionDeLlamada para la campana que se pasa por parámetro.
        """

        self._drop_tabla_temporal_si_existe()

        self._crear_tabla_temporal_desde_cdr(campana)

        self._insertar_duracion_de_llamdas(campana)
