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

    NOMBRE_TABLA_TEMPORAL = "CDR_TEMPORAL"

    def _validar_estado_correcto_de_campana(self, campana):
        """
        Valida que la campana se encuentre en el estado correcto. De lo
        contrario podrían no existir los registros de EventoDeContacto de esta
        campana y no se podría crear las DuracionDeLlamada.
        """

        # TODO: Implementar.

        return True

    def _drop_tabla_temporal_si_existe(self):
        cursor = connection.cursor()
        sql = """DROP TABLE IF EXISTS %s"""
        params = [self.NOMBRE_TABLA_TEMPORAL]

        with log_timing(logger, "_drop_tabla_temporal_si_existe tardo %s seg"):
            cursor.execute(sql, params)

    def _crear_tabla_temporal_desde_cdr(self, campana):

        cursor = connection.cursor()
        sql = """CREATE TABLE {0} AS SELECT
        CAST(substring(channel from '_(\d+)$') as integer) as campana_id,
        CAST(substring(dcontext from '(\d+)') as integer) as contacto_id,
        substring(dcontext from '-(\d+)-') as numero_telefono,
        duration as duracion_en_segundos,
        FROM cdr
        WHERE channel = 'FTS_local_campana_%s'
        """
        params = [campana.id]

        with log_timing(logger,
                        "_crear_tabla_temporal_desde_cdr() tardo %s seg"):
            cursor.execute(sql, params)

    def _insertar_duracion_de_llamdas(self, campana):

        cursor = connection.cursor()
        sql = """INSERT INTO fts_web_duraciondellamada
        (fecha_hora_llamada, duracion_en_segundos, campana_id, numero_telefono)
        SELECT
        fts_daemon_eventodecontacto.fecha_hora_llamada,
        %('tabla_temporal')s.duracion_en_segundos,
        %('tabla_temporal')s.campana_id,
        %('tabla_temporal')s.numero_telefono
        FROM  fts_daemon_eventodecontacto
        INNER JOIN %('tabla_temporal')s ON
        fts_daemon_eventodecontacto.contacto_id =
        %('tabla_temporal')s.contacto_id
        WHERE fts_daemon_eventodecontacto.campana_id = %('campana_id')s
        AND fts_daemon_eventodecontacto.evento IN (%('evento_answer')s)
        """
        params = [{'tabla_temporal': self.NOMBRE_TABLA_TEMPORAL,
                   'campana_id': campana.id, 'evento_answer':
                   EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_ANSWER}]

    def generar_duracion_de_llamdas_para_campana(self, campana):
        """
        Genera las DuracionDeLlamada para la campana. Es llamado desde el
        proceso de depuración de la campana.

        Supone que el cdr esta completo para la campana y existen todos los
        registros de las llamdas contestadas.
        """

        self._validar_estado_correcto_de_campana(campana)

        self._drop_tabla_temporal_si_existe()

        self._crear_tabla_temporal_desde_cdr(campana)

        self._insertar_duracion_de_llamdas(campana)
