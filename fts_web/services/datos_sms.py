# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import connection
from fts_web.models import CampanaSms
from fts_web.utiles import log_timing

import logging as _logging


logger = _logging.getLogger(__name__)


class FtsWebContactoSmsManager():
    """
    Manager de la fts_web_contacto_{0} donde cero es el id de la CampanaSms
    """
    def crear_tabla_de_fts_web_contacto(self, campana_sms_id):
        """
        Este método se encarga de hacer la depuración de los eventos de
        una campaña.
        """

        campana_sms = CampanaSms.objects.get(pk=campana_sms_id)

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms.pk))

        cursor = connection.cursor()
        sql = """CREATE TABLE {0} AS
            SELECT * FROM fts_web_contacto
            WHERE bd_contacto_id = %s
            WITH DATA
        """.format(nombre_tabla)

        params = [campana_sms.bd_contacto.pk]
        with log_timing(logger,
            "crear_tabla_de_fts_web_contacto tardo %s seg"):
            cursor.execute(sql, params)

        # Ahora realiza la creacion de los otros campos faltantes
        self._alter_table_fts_web_contacto(campana_sms.id)

        # ahora update el campo destino
        sql = """UPDATE {0}
            SET destino=substring(datos from 3 for
            position('\"' in substring(datos from 3 for 50))-1  )
        """.format(nombre_tabla)

        with log_timing(logger,
            "update destino tardo %s seg"):
            cursor.execute(sql)


    def _alter_table_fts_web_contacto(self, campana_sms_id):
        """
        Crea campos faltantes en la tabla fts_web_contactos
        """

        campana_sms = CampanaSms.objects.get(pk=campana_sms_id)

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms.pk))

        cursor = connection.cursor()
        sql = """ALTER TABLE {0}
            ADD sms_enviado smallint default 0
        """.format(nombre_tabla)

        with log_timing(logger,
            "ALTER_TABLE: De sms_enviado tardo %s seg"):
            cursor.execute(sql)

        sql = """ALTER TABLE {0}
            ADD sms_enviado_fecha timestamp
        """.format(nombre_tabla)

        with log_timing(logger,
            "ALTER_TABLE: De sms_enviado_fecha tardo %s seg"):
            cursor.execute(sql)

        sql = """ALTER TABLE {0}
            ADD destino char(20)
        """.format(nombre_tabla)

        with log_timing(logger,
            "ALTER_TABLE: destino tardo %s seg"):
            cursor.execute(sql)

        sql = """ALTER TABLE {0}
            ADD campana_sms_id integer default %s
        """.format(nombre_tabla)

        params = [campana_sms.id]
        with log_timing(logger,
            "ALTER_TABLE: campana_sms_id tardo %s seg"):
            cursor.execute(sql, params)

        sql = """ALTER TABLE {0}
            ADD cant_intentos integer default 0
        """.format(nombre_tabla)

        with log_timing(logger,
            "ALTER_TABLE: cant_intentos tardo %s seg"):
            cursor.execute(sql)

