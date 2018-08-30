# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.conf import settings
from django.db import connection
from fts_web.models import CampanaSms
from fts_web.utiles import log_timing

import logging as _logging


logger = _logging.getLogger(__name__)


class FtsWebContactoSmsManager():
    """
    Manager de la fts_web_contacto_{0} donde cero es el id de la CampanaSms
    """

    # ESTADOS de envio de sms
    ESTADO_ENVIO_NO_PROCESADO = 0
    ESTADO_ENVIO_ENVIADO = 1
    ESTADO_ENVIO_SIN_CONFIRMACION = 2
    ESTADO_ENVIO_ERROR_ENVIO = -1
    ESTADO_ENVIO_NO_HAY_MODEM = - 2

    MAP_ESTADO_ENVIO_A_LABEL = {
        ESTADO_ENVIO_NO_PROCESADO: 'No procesado',
        ESTADO_ENVIO_ENVIADO: 'Enviado correctamente',
        ESTADO_ENVIO_ERROR_ENVIO: 'Error en el envio',
        ESTADO_ENVIO_SIN_CONFIRMACION: 'Enviado sin confirmacion',
        ESTADO_ENVIO_NO_HAY_MODEM: 'No hay modem disponible',
    }

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
        # Fixme: ojo que si en el primer campo de la base datos no esta el
        # telefono guarda cualquier cosa
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

        if settings.FTS_SMS_UTILIZADO == 'gateway':
            sql = """ALTER TABLE {0}
                ADD puerto integer
            """.format(nombre_tabla)

            with log_timing(logger,
                "ALTER_TABLE: puerto tardo %s seg"):
                cursor.execute(sql)

    def eliminar_tabla_fts_web_contacto(self, campana_sms):
        """
        Este método se encarga de eliminar la tabla de fts_web_contacto_xx
        que se genero en por el demonio sms.

        Este método se invoca en la eliminación de la campaña.
        """

        assert isinstance(campana_sms, CampanaSms)
        assert isinstance(campana_sms.pk, int)

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms.pk))

        cursor = connection.cursor()
        sql = """DROP TABLE {0}""".format(nombre_tabla)

        params = [campana_sms.pk]
        with log_timing(logger,
            "Eliminación tabla fts_web_contacto: Proceso de eliminación de la "
            " tabla fts_web_contacto tardo:  %s seg"):
            cursor.execute(sql, params)


class RecicladorContactosCampanaSMS():
    """
    Este manager se encarga de obtener los contactos según el tipo de
    reciclado de campana de sms que se realice.
    """

    def obtener_contactos_reciclados(self, campana_sms, tipos_reciclado):
        """
        Este método se encarga de iterar sobre los tipos de reciclado que
        se indiquen aplicar en el reciclado de campana. Según el tipo de
        reciclado se invoca al método adecuado para llevar a cabo la consulta
        correspondiente, y en caso de que sea mas de uno se sumarizan las
        mismas.
        """
        contactos_reciclados = set()
        for tipo_reciclado in tipos_reciclado:
            if int(tipo_reciclado) == CampanaSms.TIPO_RECICLADO_ERROR_ENVIO:
                contactos_reciclados.update(
                    self._obtener_contactos_error_envio(campana_sms))
            elif int(tipo_reciclado) == CampanaSms.TIPO_RECICLADO_ENVIADO_SIN_CONFIRMACION:
                contactos_reciclados.update(
                    self._obtener_contactos_enviado_sin_confirmacion(
                        campana_sms))
            else:
                assert False, "El tipo de reciclado es invalido: {0}".format(
                    tipo_reciclado)
        return contactos_reciclados

    def _obtener_contactos_error_envio(self, campana_sms):
        """
        Este método se encarga de devolver los contactos que tengan el
        error en el envio de del sms
        El -1 significa error del envio en el codigo de daniel
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms.pk))

        cursor = connection.cursor()
        sql = """SELECT datos
            FROM  {0}
            WHERE sms_enviado = -1
            GROUP BY id, datos
        """.format(nombre_tabla)

        with log_timing(logger,
                        "_obtener_contactos_error_envio() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        return values

    def _obtener_contactos_enviado_sin_confirmacion(self, campana_sms):
        """
        Este método se encarga de devolver los contactos que tengan el
        error en el envio de del sms
        El -1 significa error del envio en el codigo de daniel
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms.pk))

        cursor = connection.cursor()
        sql = """SELECT datos
            FROM  {0}
            WHERE sms_enviado = %s
            GROUP BY id, datos
        """.format(nombre_tabla)

        params = [FtsWebContactoSmsManager.ESTADO_ENVIO_SIN_CONFIRMACION]

        with log_timing(logger,
                        "_obtener_contactos_enviado_sin_confirmacion() tardo %s seg"):
            cursor.execute(sql, params)
            values = cursor.fetchall()

        return values


class EstadisticasContactoReporteSms():

    def obtener_contacto_sms_enviado(self, campana_sms_id):
        """
        Este método se encarga de devolver los contactos
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms_id))

        cursor = connection.cursor()
        sql = """SELECT id, sms_enviado_fecha, destino, sms_enviado, datos
            FROM  {0}
            WHERE campana_sms_id = %s
        """.format(nombre_tabla)

        params = [campana_sms_id]

        with log_timing(logger,
                        "obtener_contacto_sms_enviado() tardo %s seg"):
            cursor.execute(sql, params)
            values = cursor.fetchall()

        return values

    def obtener_contacto_sms_enviado_gateway(self, campana_sms_id):
        """
        Este método se encarga de devolver los contactos enviado por gateway
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms_id))

        cursor = connection.cursor()
        sql = """SELECT id, sms_enviado_fecha, destino, sms_enviado, datos,
            puerto FROM  {0}
            WHERE campana_sms_id = %s
        """.format(nombre_tabla)

        params = [campana_sms_id]

        with log_timing(logger,
                        "obtener_contacto_sms_enviado_gateway() tardo %s seg"):
            cursor.execute(sql, params)
            values = cursor.fetchall()

        return values

    def obtener_contacto_sms_repuesta_esperada(self, campana_sms_id):
        """
        Este método se encarga de devolver los contactos
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms_id))

        cursor = connection.cursor()
        sql = """SELECT DISTINCT c.id, \"SenderNumber\",  c.sms_enviado_fecha,
            \"UpdatedInDB\",  \"TextDecoded\"
            FROM  {0} c INNER JOIN inbox
            ON \"SenderNumber\" like concat('%',
            substring(c.destino from 7 for 50) ) AND \"UpdatedInDB\" >
            c.sms_enviado_fecha INNER JOIN fts_web_opcionsms o ON
            o.campana_sms_id=c.campana_sms_id AND \"TextDecoded\" like
            concat('%',o.respuesta,'%')
            """.format(nombre_tabla)

        params = [campana_sms_id]

        with log_timing(logger,
                        "obtener_contacto_sms_repuesta_esperada()"
                        "tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        return values

    def obtener_contacto_sms_repuesta_invalida(self, campana_sms_id, hora_desde,
                                               hora_hasta):
        """
        Este método se encarga de devolver los contactos
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms_id))

        cursor = connection.cursor()
        sql = """SELECT DISTINCT c.id, \"SenderNumber\",  c.sms_enviado_fecha,
            \"UpdatedInDB\",  \"TextDecoded\"
            FROM  {0} c INNER JOIN inbox
            ON \"SenderNumber\" like concat('%%',
            substring(c.destino from 7 for 50) ) AND \"UpdatedInDB\" >
            ( c.sms_enviado_fecha + INTERVAL %(hora_desde)s) AND "UpdatedInDB" <
            ( c.sms_enviado_fecha + INTERVAL %(hora_hasta)s  ) LEFT JOIN
            fts_web_opcionsms o ON o.campana_sms_id=c.campana_sms_id AND
            \"TextDecoded\" like concat('%%',o.respuesta,'%%')
            """.format(nombre_tabla)

        hora_hasta = str(hora_hasta) + " hour"
        hora_desde = str(hora_desde) + " hour"

        params = {
            'hora_desde': hora_desde,
            'hora_hasta': hora_hasta,

        }

        with log_timing(logger,
                        "obtener_contacto_sms_repuesta_invalida()"
                        "tardo %s seg"):
            cursor.execute(sql, params)
            values = cursor.fetchall()

        return values

    def obtener_count_contactos_estado(self, campana_sms_id):
        """
        Este método se encarga de devolver una lista con informacion del
         total de los eventos(no procesado, error envio y enviado)
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms_id))

        cursor = connection.cursor()
        sql = """SELECT sms_enviado, count(*)
            FROM  {0}
            group by sms_enviado
        """.format(nombre_tabla)

        contacto_manager = FtsWebContactoSmsManager()

        params = [contacto_manager.ESTADO_ENVIO_ENVIADO]

        with log_timing(logger,
                        "obtener_count_contactos_estado() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        return values

    def obtener_total_contacto_sms_repuesta_esperada(self, campana_sms_id):
        """
        Este método se encarga de devolver el total de los contactos con
        sms repuesta esperada
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms_id))

        cursor = connection.cursor()
        sql = """SELECT DISTINCT count(*)
            FROM  {0} c INNER JOIN inbox
            ON \"SenderNumber\" like concat('%',
            substring(c.destino from 7 for 50) ) AND \"UpdatedInDB\" >
            c.sms_enviado_fecha INNER JOIN fts_web_opcionsms o ON
            o.campana_sms_id=c.campana_sms_id AND \"TextDecoded\" like
            concat('%',o.respuesta,'%')
            """.format(nombre_tabla)

        with log_timing(logger,
                        "obtener_total_contacto_sms_repuesta_esperada()"
                        "tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        return values

    def obtener_total_contacto_sms_repuesta_invalida(self, campana_sms_id):
        """
        Este método se encarga de devolver el total delos contactos
        con sms respuesta invalida
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms_id))

        cursor = connection.cursor()
        sql = """SELECT DISTINCT count(*)
            FROM  {0} c INNER JOIN inbox i
            ON \"SenderNumber\" like concat('%',
            substring(c.destino from 7 for 50) ) AND \"UpdatedInDB\" >
            c.sms_enviado_fecha LEFT JOIN fts_web_opcionsms o ON
            o.campana_sms_id=c.campana_sms_id AND \"TextDecoded\" not like
            concat('%',o.respuesta,'%')
            """.format(nombre_tabla)

        with log_timing(logger,
                        "obtener_total_contacto_sms_repuesta_invalida()"
                        "tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        return values

    def obtener_total_supervision(self, campana_sms_id):
        """
        Este método se encarga de devolver el totales de la superviion
        """

        nombre_tabla = "fts_web_contacto_{0}".format(int(campana_sms_id))

        cursor = connection.cursor()
        sql = """SELECT 0 as estado, count(*)
            FROM  {0}
            WHERE sms_enviado = 0

            UNION SELECT 1 as estado, count(*)
            FROM  {0}
            WHERE sms_enviado = 1

            UNION SELECT -1 as estado, count(*)
            FROM  {0}
            WHERE sms_enviado = -1

            UNION SELECT 2 as estado, count(*)
            FROM  {0}
            WHERE sms_enviado = 2

            UNION SELECT DISTINCT 3 as estado, count(*)
            FROM  {0} c INNER JOIN inbox
            ON \"SenderNumber\" like concat('%',
            substring(c.destino from 7 for 50) ) AND \"UpdatedInDB\" >
            c.sms_enviado_fecha INNER JOIN fts_web_opcionsms o ON
            o.campana_sms_id=c.campana_sms_id AND \"TextDecoded\" like
            concat('%',o.respuesta,'%')

            UNION SELECT DISTINCT 4 as estado, count(*)
            FROM  {0} c INNER JOIN inbox i
            ON \"SenderNumber\" like concat('%',
            substring(c.destino from 7 for 50) ) AND \"UpdatedInDB\" >
            c.sms_enviado_fecha LEFT JOIN fts_web_opcionsms o ON
            o.campana_sms_id=c.campana_sms_id AND \"TextDecoded\" not like
            concat('%',o.respuesta,'%')

            """.format(nombre_tabla)

        with log_timing(logger,
                        "obtener_total_supervision()"
                        "tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        return values