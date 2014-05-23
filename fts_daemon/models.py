# -*- coding: utf-8 -*-
"""
Modelos usados por el Daemon y el proxy AGI.


"""

from __future__ import unicode_literals

from collections import defaultdict

from django.conf import settings
from django.db import connection
from django.db import models
from django.db.models import Count
from django.db.models.aggregates import Max

from fts_web.models import Campana, BaseDatosContacto, Contacto
from fts_web.utiles import log_timing
import logging as _logging


logger = _logging.getLogger(__name__)


#==============================================================================
# EventoDeContacto
#==============================================================================

class EventoDeContactoManager(models.Manager):
    """Manager para EventoDeContacto"""

    def _check_intento(self, intento):
        if settings.DEBUG or settings.FTS_TESTING_MODE:
            assert intento >= 1, "intento debe ser >= 1"
        else:
            if intento < 1 or intento > 10:
                logger.warn("Se utilizo un valor de intento sospechoso: %s",
                    intento)

    def inicia_intento(self,
        campana_id, contacto_id, intento_actual):
        """Crea evento EVENTO_DAEMON_INICIA_INTENTO.

        :param intento_actual: número correspondiente a qué
        intento corresponde este evento, o sea, si es el 1er intento,
        intento valdrá 1. Debe ser >= 1
        """
        self._check_intento(intento_actual)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO,
            dato=intento_actual)

    def create_evento_daemon_originate_successful(self,
        campana_id, contacto_id, intento_actual):
        """Crea evento EVENTO_DAEMON_ORIGINATE_SUCCESSFUL

        :param intento_actual: número correspondiente a qué
        intento corresponde este evento, o sea, si es el 1er intento,
        intento valdrá 1. Debe ser >= 1
        """
        self._check_intento(intento_actual)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_DAEMON_ORIGINATE_SUCCESSFUL,
            dato=intento_actual)

    def create_evento_daemon_originate_failed(self,
        campana_id, contacto_id, intento_actual):
        """Crea evento EVENTO_DAEMON_ORIGINATE_FAILED

        :param intento_actual: número correspondiente a qué
        intento corresponde este evento, o sea, si es el 1er intento,
        intento valdrá 1. Debe ser >= 1
        """
        self._check_intento(intento_actual)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_DAEMON_ORIGINATE_FAILED,
            dato=intento_actual)

    def create_evento_daemon_originate_internal_error(self,
        campana_id, contacto_id, intento_actual):
        """Crea evento
        EventoDeContacto.EVENTO_DAEMON_ORIGINATE_INTERNAL_ERROR

        :param intento_actual: número correspondiente a qué
        intento corresponde este evento, o sea, si es el 1er intento,
        intento valdrá 1. Debe ser >= 1
        """
        self._check_intento(intento_actual)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_DAEMON_ORIGINATE_INTERNAL_ERROR,
            dato=intento_actual)

    def dialplan_local_channel_pre_dial(self, campana_id, contacto_id,
        intento_actual):
        """Crea evento
        EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO

        :param intento_actual: número correspondiente a qué
        intento corresponde este evento, o sea, si es el 1er intento,
        intento valdrá 1. Debe ser >= 1
        """
        self._check_intento(intento_actual)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO,
            dato=intento_actual)

    def dialplan_local_channel_post_dial(self, campana_id, contacto_id,
        intento_actual, ev):
        """Crea evento asociado a resultado de Dial() / DIALSTATUS

        :param intento_actual: número correspondiente a qué
        intento corresponde este evento, o sea, si es el 1er intento,
        intento valdrá 1. Debe ser >= 1
        """
        self._check_intento(intento_actual)
        if not ev in EventoDeContacto.DIALSTATUS_MAP.values():
            logger.warn("dialplan_local_channel_post_dial(): se recibio "
                "evento que no es parte de DIALSTATUS_MAP: %s", ev)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=ev,
            dato=intento_actual)

    def dialplan_campana_iniciado(self, campana_id, contacto_id,
        intento_actual):
        """Crea evento
        EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO

        :param intento_actual: número correspondiente a qué
        intento corresponde este evento, o sea, si es el 1er intento,
        intento valdrá 1. Debe ser >= 1
        """
        self._check_intento(intento_actual)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO,
            dato=intento_actual)

    def dialplan_campana_finalizado(self, campana_id, contacto_id,
        intento_actual):
        """Crea evento
        EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_FINALIZADO

        :param intento_actual: número correspondiente a qué
        intento corresponde este evento, o sea, si es el 1er intento,
        intento valdrá 1. Debe ser >= 1
        """
        self._check_intento(intento_actual)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_ASTERISK_DIALPLAN_CAMPANA_FINALIZADO,
            dato=intento_actual)

    def fin_err_i(self, campana_id, contacto_id, intento_actual):
        """Crea evento
        EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_I

        :param intento_actual: número correspondiente a qué
        intento corresponde este evento, o sea, si es el 1er intento,
        intento valdrá 1. Debe ser >= 1
        """
        self._check_intento(intento_actual)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_I,
            dato=intento_actual)

    def fin_err_t(self, campana_id, contacto_id, intento_actual):
        """Crea evento
        EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_T

        :param intento_actual: número correspondiente a qué
        intento corresponde este evento, o sea, si es el 1er intento,
        intento valdrá 1. Debe ser >= 1
        """
        self._check_intento(intento_actual)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=EventoDeContacto.\
                EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_T,
            dato=intento_actual)

    def opcion_seleccionada(self, campana_id, contacto_id,
        intento_actual, evento):
        """Crea evento EventoDeContacto.EVENTO_ASTERISK_OPCION_X.

        :param intento_actual: número correspondiente a qué
        intento corresponde este evento, o sea, si es el 1er intento,
        intento valdrá 1. Debe ser >= 1
        :param evento: el evento asociado al numero (uno entre
                       EVENTO_ASTERISK_OPCION_0 y EVENTO_ASTERISK_OPCION_9
        :type evento: int
        """
        self._check_intento(intento_actual)
        return self.create(campana_id=campana_id,
            contacto_id=contacto_id,
            evento=evento,
            dato=intento_actual)

    def get_eventos_finalizadores(self):
        """Devuelve eventos que permiten marcar una llamada como
        finalizada, o sea, que ya no debe ser tendia en cuenta
        al realizar futuras llamadas para la campaña.
        """
        values = []
        for name in settings.FTS_EVENTOS_FINALIZADORES:
            assert name in dir(EventoDeContacto)
            values.append(getattr(EventoDeContacto, name))
        return values

    def get_nombre_de_evento(self, evento_id):
        # TODO: cachear estas cosas pre-procesadas!
        _cached = getattr(self, '__map_nombres_de_evento', None)
        if not _cached:
            names = [const for const in dir(EventoDeContacto)
                if const.startswith("EVENTO_")]
            names = [const for const in names
                if type(getattr(EventoDeContacto, const)) == int]
            _cached = dict([(getattr(EventoDeContacto, const), const)
                for const in names])
            self.__map_nombres_de_evento = _cached
        return _cached.get(evento_id, None)


class SimuladorEventoDeContactoManager():
    """Simula acciones. Estos metodos son utilizados para pruebas,
    o simular distintas acciones, pero NO deben utilizarse
    en produccion.

    Tambien tiene metodos utilizados en scripst de pruebas
    y tests cases.
    """

    def simular_realizacion_de_intentos(self, campana_id, intento,
        probabilidad=0.33):
        """
        Crea eventos EVENTO_DAEMON_INICIA_INTENTO para contactos de
        una campana.

        :param intento: A que intento de contaco pertenece la simulación
                        del evento. Intento == 1 es el 1er intento.
        :type intento: int
        :param probabilidad: Para que porcentage (aprox) de los contactos hay
                             que crear intentos. Para crear intentos para
                             TODOS, usar valor mayor a 1.0
        :type probabilidad: float
        """
        assert settings.DEBUG or settings.FTS_TESTING_MODE
        return self.simular_evento(campana_id,
            evento=EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO,
            intento=intento,
            probabilidad=probabilidad)

    def simular_evento(self, campana_id, intento, evento, probabilidad=0.33):
        """
        Crea evento para contactos de una campana.
        :param intento: A que intento de contaco pertenece la simulación
                        del evento. Intento == 1 es el 1er intento.
        :type intento: int
        :param probabilidad: Para que porcentage (aprox) de los contactos hay
                             que crear eventos. Para crear intentos para TODOS,
                             usar valor mayor a 1.0
        :type probabilidad: float
        :param evento Evento a insertar
        :type evento: int
        """
        assert settings.DEBUG or settings.FTS_TESTING_MODE
        campana = Campana.objects.get(pk=campana_id)
        cursor = connection.cursor()
        # TODO: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """
        INSERT INTO fts_daemon_eventodecontacto
            SELECT
                nextval('fts_daemon_eventodecontacto_id_seq') as "id",
                {campana_id} as "campana_id",
                contacto_id as "contacto_id",
                NOW() as "timestamp",
                {evento} as "evento",
                {intento} as "dato"
            FROM
                (
                    SELECT DISTINCT contacto_id as "contacto_id"
                        FROM fts_daemon_eventodecontacto
                        WHERE campana_id = {campana_id}
                            AND random() <= {probabilidad}
                ) as "contacto_id"
        """.format(campana_id=campana.id,
                evento=int(evento),
                probabilidad=float(probabilidad),
                intento=intento)

        with log_timing(logger,
            "simular_realizacion_de_intentos() tardo %s seg"):
            cursor.execute(sql)

    def crear_bd_contactos_con_datos_random(self, cantidad):
        """Crea BD con muchos contactos"""
        assert settings.DEBUG or settings.FTS_TESTING_MODE
        bd_contactos = BaseDatosContacto.objects.create(
            nombre="PERF - {0} contactos".format(cantidad),
            archivo_importacion='inexistete.csv',
            nombre_archivo_importacion='inexistete.csv',
            sin_definir=False,
            columna_datos=1
        )

        cursor = connection.cursor()
        # TODO: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """
            INSERT INTO fts_web_contacto
                SELECT
                    nextval('fts_web_contacto_id_seq') as "id",
                    (random()*1000000000000)::bigint::text as "telefono",
                    '' as "datos",
                    {0} as "bd_contacto_id"
                FROM
                    generate_series(1, {1})
        """.format(bd_contactos.id, cantidad)

        with log_timing(logger,
            "crear_bd_contactos_con_datos_random() tardo %s seg"):
            cursor.execute(sql)
        return bd_contactos


class EventoDeContactoEstadisticasManager():
    """Devuelve información resumida de eventos"""

    def obtener_count_intentos(self, campana_id):
        """Devuelve una lista de listas con información de intentos
        realizados, ordenados por cantidad de intentos (ej: 1, 2, etc.)

        Los elementos de la lista devuelta son listas, que contienen
        dos elementos:

        1. cantidad de intentos (1, 2, etc)
        2. count, cantidad de contactos que poseen esa cantidad
           de intentos

        Ejemplo: _((1, 721,), (2, 291,))_ 721 contactos fueron
        intentados 1 vez, 291 contactos 2 veces
        """
        campana = Campana.objects.get(pk=campana_id)
        cursor = connection.cursor()
        # FIXME: PERFORMANCE: quitar sub-select
        # FIXME: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """SELECT DISTINCT ev_count, count(*) FROM
            (
                SELECT count(*) AS "ev_count"
                FROM fts_daemon_eventodecontacto
                WHERE evento = {evento} and campana_id = {campana_id}
                GROUP BY contacto_id
            ) AS "ev_count"
            GROUP BY ev_count
            ORDER BY 1
        """.format(campana_id=campana.id,
            evento=EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO)

        with log_timing(logger, "obtener_count_intentos() "
            "tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()
        return values

    def obtener_count_eventos(self, campana_id):
        """Devuelve una lista de listas con información de count de eventos
        para una campana.

        Ejemplo: _((1, 412,), (2, 874,))_ implica que hay 412 eventos
        del tipo '1', 874 eventos de tipo '2'.
        """
        campana = Campana.objects.get(pk=campana_id)
        cursor = connection.cursor()
        # FIXME: PERFORMANCE: quitar sub-select
        # FIXME: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """SELECT evento, count(*)
            FROM fts_daemon_eventodecontacto
            WHERE campana_id = {0}
            GROUP BY evento
            ORDER BY 1
        """.format(campana.id)

        cursor.execute(sql)
        with log_timing(logger,
            "obtener_count_eventos() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()
        return values

    def obtener_array_eventos_por_contacto(self, campana_id):
        """Devuelve una lista de listas con array de eventos para
        cada contacto.

        Ejemplo: _((783474, {1,22,13}, dt1), (8754278, {1,17,}, dt2))_
        implica que hay eventos de 2 contactos (783474 y 8754278), y los
        tipos de eventos son los indicados en los arrays. `dt` es el
        datetime del ultimo evento registrado.
        """
        campana = Campana.objects.get(pk=campana_id)
        cursor = connection.cursor()
        # FIXME: PERFORMANCE: quitar sub-select
        # FIXME: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """SELECT contacto_id AS "contacto_id", array_agg(evento),
                    max(timestamp)
            FROM fts_daemon_eventodecontacto
            WHERE campana_id = {campana_id}
            GROUP BY contacto_id;
        """.format(campana_id=campana.id)

        cursor.execute(sql)
        with log_timing(logger,
            "obtener_array_eventos_por_contacto() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()
        return values

    def obtener_estadisticas_de_campana(self, campana_id):
        """Procesa estadisticas para una campana.

        Devuelve 3 dicts con estadísticas:

        1. ``counter_x_estado``: cuantos contactos estan en los distintos
           estados (definidos más abajo)
        2. ``counter_intentos``: cuantos contactos se han intentado distinta
           cantidad de veces.
        3. ``counter_por_evento``: cuantos eventos de cada tipo fueron
           producidos por los contactos

        counter_x_estado

        - ``counter_x_estado['finalizado_x_evento_finalizador']``: cantidad de
          contactos que ya están finalizados, o sea, no se intentará
          contactarlos, porque ya posee uno de los eventos finalizadores.
          Tomamos estos casos como contactos realizados exitosamente
          (sin importar si escucharon todo el mensaje, o ha seleccionado
          o no alguna opción).
        - ``counter_x_estado['finalizado_x_limite_intentos']``: cantidad de
          contactos que ya están finalizados, o sea, no se intentará
          contactarlos, porque ya se intentó contactarlos varias veces, y
          se llegó al límite de intentos definido en la campaña.
        - ``counter_x_estado['pendientes']``: cuantos contactos quedan
          pendientes por contactar.
        - ``counter_x_estado['no_intentados']``: para cuántos contactos no
          existen intentos de contacto, o sea, nunca se intentó contactarlos.
        - ``counter_x_estado['no_selecciono_opcion']``: cuántos contactos
          fueron contactados, pero NO seleccionaron ninguna opción.

        counter_intentos

        - ``counter_intentos[0]``: para cuántos contactos no existen intentos
          de contacto, o sea, nunca se intentó contactarlos.
        - ``counter_intentos[1]``: para cuántos contactos existen 1 intento
          de contacto.
        - ``counter_intentos[n]``: para cuántos contactos existen `n` intento
          de contacto. Este valor nunca debería ser mayor al límite de
          contactos establecido en la campaña.

        counter_por_evento

        - ``counter_por_evento[5]``: cuantos eventos de tipo '5' existen
        - ``counter_por_evento[41]``: cuantos eventos de tipo '41' existen
        - ``counter_por_evento[n]``: cuantos eventos de tipo `n` existen
        """
        campana = Campana.objects.get(pk=campana_id)
        array_eventos_por_contacto = self.obtener_array_eventos_por_contacto(
            campana_id)
        finalizadores = EventoDeContacto.objects.get_eventos_finalizadores()

        # counter_finalizados ««« ELIMINAR!
        counter_x_estado = {
            'finalizado_x_evento_finalizador': 0,
            'finalizado_x_limite_intentos': 0,
            'pendientes': 0,
            'no_selecciono_opcion': 0,
        }

        counter_intentos = defaultdict(lambda: 0)
        counter_por_evento = defaultdict(lambda: 0)

        # item[0] -> contact_id / item[1] -> ARRAY / item[2] -> timestamp
        for _, array_eventos, _ in array_eventos_por_contacto:
            eventos = set(array_eventos)

            ## Chequeamos cantidad de intentos
            cant_intentos = len([ev for ev in array_eventos
                if ev == EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO])
            counter_intentos[cant_intentos] += 1

            ## Chequea finalizados y no finalizados
            finalizado = False
            for finalizador in finalizadores:
                if finalizador in eventos:
                    finalizado = True
                    break

            # TODO: unificar en iterador de más arriba
            for evento in array_eventos:
                # FIXME: aqui es un buen lugar donde ignorar eventos
                # Ej: si elige más de 1 opcion, y hace falta que solo
                #  se tenga en cuenta la 1era elegida
                # (suponiendo que 'array_eventos' esta ordenado)
                counter_por_evento[evento] += 1

            if finalizado:
                counter_x_estado['finalizado_x_evento_finalizador'] += 1
            else:
                if cant_intentos >= campana.cantidad_intentos:
                    counter_x_estado['finalizado_x_limite_intentos'] += 1
                else:
                    counter_x_estado['pendientes'] += 1

            #Calcula la cantidad de contactos que no seleccionaron ninguna
            #opción de la campaña. Siempre que el contacto haya contestado.
            if finalizado:
                opciones = EventoDeContacto.NUMERO_OPCION_MAP.values()
                if not any(opcion in eventos for opcion in opciones):
                    counter_x_estado['no_selecciono_opcion'] += 1

        return counter_x_estado, counter_intentos, counter_por_evento

    def obtener_contadores_por_intento(self, campana_id, cantidad_intentos,
        timestamp_ultimo_evento):
        """
        Se encarga de obtener los contadores de ciertos eventos, por cada
        intento de contacto de la campana.

        :param campana_id: De que campana se contabilizan los eventos.
        :type campana_id: int
        :param cantidad_intentos: El limite de intentos para la  campana.
        :type cantidad_intentos: int
        :param timestamp_ultimo_evento: Desde que timestamp hasta hoy ahora se
        tienen que filtrar los eventos para la campana pasada.
        :type timestamp_ultimo_evento: datetime
        """

        if timestamp_ultimo_evento:
            #Si viene el timestamp_ultimo_evento, se filtran los eventos de la
            #campana_id desde ese momento hasta hoy y ahora.
            EDC = EventoDeContacto.objects.filter(campana_id=campana_id,
                timestamp__gt=timestamp_ultimo_evento)
        else:
            #Si no viene el timestamp_ultimo_evento, se filtran todos los
            #eventos de la campana_id.
            EDC = EventoDeContacto.objects.filter(campana_id=campana_id)

        #En el caso que no se encuentren eventos para la campana, esto ocurre
        #cuando desde el último evento que se tomo (timestamp_ultimo_evento)
        #hasta hoy y ahora no hay eventos registrados.
        if not EDC.count():
            return None

        #Obtiene el timestamp del último evento filtrado para la campana_id.
        timestamp_ultimo_evento = EDC.latest('timestamp').timestamp

        #Por cada intento de la campana_id, cuenta lo diferentes eventos y los
        #va agregando a un diccionario, que es lo que devuelve el método.
        dic_contadores = {}
        for numero_intento in range(1, cantidad_intentos + 1):
            cantidad_intentos = EDC.filter(
                dato=numero_intento,
                evento=EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO,
            ).count()

            finalizados = EDC.filter(
                dato=numero_intento,
                evento__in=EventoDeContacto.objects.get_eventos_finalizadores(),
            )
            cantidad_finalizados = finalizados.count()

            ##Comento la obtención de la cantidad que no seleccionaron
            # una opción, porque por ahora involucra hacer una consulta
            # sobre toda la tabla.

            # cantidad_seleccionaron_opcion = 0
            # cantidad_no_seleccionaron_opcion = 0
            # for finalizado in finalizados:
            #     opciones_seleccionadas = EventoDeContacto.objects.filter(
            #         contacto_id=finalizado.contacto_id,
            #         evento__in=EventoDeContacto.NUMERO_OPCION_MAP.values(),
            #     )
            #     if not opciones_seleccionadas:
            #         cantidad_no_seleccionaron_opcion += 1
            #     else:
            #         cantidad_seleccionaron_opcion += 1

            cantidad_x_opcion = EDC.filter(
                campana_id=campana_id,
                dato=numero_intento,
                evento__in=EventoDeContacto.NUMERO_OPCION_MAP.values(),
            ).values('evento').annotate(cantidad=Count('evento'))

            dic_contadores.update({numero_intento:
                {'cantidad_intentos': cantidad_intentos,
                'cantidad_finalizados': cantidad_finalizados,
                'cantidad_x_opcion': cantidad_x_opcion,
                #'cantidad_seleccionaron_opcion': cantidad_seleccionaron_opcion,
                #'cantidad_no_seleccionaron_opcion':\
                #    cantidad_no_seleccionaron_opcion,
                'timestamp_ultimo_evento': timestamp_ultimo_evento,
                }
            })
        return dic_contadores


class GestionDeLlamadasManager(models.Manager):
    """Manager para EventoDeContacto, con la funcionalidad
    que es utilizada para la gestión más basica de las llamadas.

    Incluye la funcionalidad de programar llamadas a realizar,
    buscar llamadas pendientes, etc.

    Esta funcionalidad es la más crítica del sistema, en cuestiones
    de robustez y performance. Todos estos metodos deben estar
    extensamenete probados.
    """

    def programar_campana(self, campana_id):
        """Crea eventos EVENTO_CONTACTO_PROGRAMADO para todos los contactos
        de la campana.

        Hace algo equivalente al viejo
        *IntentoDeContacto.objects.crear_intentos_para_campana()*.
        """
        programar_campana_func = getattr(self,
            settings.FTS_PROGRAMAR_CAMPANA_FUNC)
        return programar_campana_func(campana_id)

    def _programar_campana_postgresql(self, campana_id):
        campana = Campana.objects.get(pk=campana_id)
        cursor = connection.cursor()

        # FIXME: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """
        INSERT INTO fts_daemon_eventodecontacto
            SELECT
                nextval('fts_daemon_eventodecontacto_id_seq') as "id",
                {campana_id} as "campana_id",
                fts_web_contacto.id as "contacto_id",
                NOW() as "timestamp",
                {evento} as "evento",
                0 as "dato"
            FROM
                fts_web_contacto
            WHERE
                bd_contacto_id = {bd_contacto_id}
        """.format(campana_id=campana.id,
            bd_contacto_id=campana.bd_contacto.id,
            evento=EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)

        with log_timing(logger, "_programar_campana_postgresql() "
            "tardo %s seg"):
            cursor.execute(sql)

    def _programar_campana_sqlite(self, campana_id):
        campana = Campana.objects.get(pk=campana_id)
        for contacto in campana.bd_contacto.contactos.all():
            EventoDeContacto.objects.create(
                campana_id=campana.id,
                contacto_id=contacto.id,
                evento=EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO,
                dato=0,
            )

    def obtener_pendientes(self, campana_id, limit=100):
        """Devuelve lista de listas, con los datos de los contactos que
        estan pendientes de realizar. Tiene en cuenta la cantidad maxima
        de intentos seteada en la campana

        Cada elemento de la lista contiene una lista, con 2 items:
        - item[0]: cantidad de veces intentado
        - item[1]: id_contacto

        Cuando todos los pendientes han sido finalizados, devuelve
        una lista vacia.
        """
        campana = Campana.objects.get(pk=campana_id)

        finalizadores = ",".join([str(int(x))
            for x in EventoDeContacto.objects.get_eventos_finalizadores()])

        # FIXME: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """
        SELECT count(*) AS "ev_count", contacto_id AS "contacto_id"
        FROM fts_daemon_eventodecontacto
        WHERE (evento = {ev_programado} OR evento = {ev_intento})
            AND campana_id = {campana_id}
            AND contacto_id NOT IN
            (
                SELECT DISTINCT tmp.contacto_id
                FROM fts_daemon_eventodecontacto AS tmp
                WHERE tmp.campana_id = {campana_id} AND
                    tmp.evento IN ({lista_eventos_finalizadores})
            )
        GROUP BY contacto_id
        HAVING count(*) < {max_intentos} + 1
        ORDER BY 1
        LIMIT {limit}
        """.format(campana_id=campana.id,
            max_intentos=campana.cantidad_intentos,
            ev_programado=EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO,
            ev_intento=EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO,
            limit=int(limit),
            lista_eventos_finalizadores=finalizadores
        )

        cursor = connection.cursor()
        with log_timing(logger,
            "_obtener_pendientes() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        values = [(row[0] - 1, row[1],) for row in values]
        return values

    def obtener_pendientes_no_en_curso(self, campana_id, contacto_ids_en_curso,
        limit=100):
        """Devuelve lista de listas, con los datos de los contactos que
        estan pendientes de realizar. Tiene en cuenta la cantidad maxima
        de intentos seteada en la campana, y filtra los contactos para
        excluir los contactos especificados en `contacto_ids_en_curso`.

        Cada elemento de la lista contiene una lista, con 2 items:
        - item[0]: cantidad de veces intentado
        - item[1]: id_contacto

        Cuando todos los pendientes han sido finalizados, devuelve
        una lista vacia.

        :param contacto_ids_en_curso: lista de ids de contactos. NO PUEDE
                                      estar vacia. Si no hay contactos
                                      en curso, utilizar obtener_pendientes()
        """

        assert len(contacto_ids_en_curso) > 0

        campana = Campana.objects.get(pk=campana_id)

        finalizadores = ",".join([str(int(x))
            for x in EventoDeContacto.objects.get_eventos_finalizadores()])

        contacto_ids_en_curso_sql = ','.join([
            str(id_cont) for id_cont in contacto_ids_en_curso])

        # FIXME: SEGURIDAD: sacar 'format()', usar api de BD
        sql = """
        SELECT count(*) AS "ev_count", contacto_id AS "contacto_id"
        FROM fts_daemon_eventodecontacto
        WHERE (evento = {ev_programado} OR evento = {ev_intento})
            AND campana_id = {campana_id}
            AND contacto_id NOT IN
            (
                {contacto_ids_en_curso}
            )
            AND contacto_id NOT IN
            (
                SELECT DISTINCT tmp.contacto_id
                FROM fts_daemon_eventodecontacto AS tmp
                WHERE tmp.campana_id = {campana_id} AND
                    tmp.evento IN ({lista_eventos_finalizadores})
            )
        GROUP BY contacto_id
        HAVING count(*) < {max_intentos} + 1
        ORDER BY 1
        LIMIT {limit}
        """.format(campana_id=campana.id,
            max_intentos=campana.cantidad_intentos,
            ev_programado=EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO,
            ev_intento=EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO,
            limit=int(limit),
            lista_eventos_finalizadores=finalizadores,
            contacto_ids_en_curso=contacto_ids_en_curso_sql
        )

        cursor = connection.cursor()
        with log_timing(logger,
            "obtener_pendientes_no_en_curso() tardo %s seg"):
            cursor.execute(sql)
            values = cursor.fetchall()

        values = [(row[0] - 1, row[1],) for row in values]
        return values

    def obtener_datos_de_contactos(self, id_contactos):
        """Devuelve los datos necesarios para generar llamadas
        para los contactos pasados por parametros (lista de IDs).

        Devuelve lista de listas, con ((id_contacto, telefono,), ...)
        """
        if len(id_contactos) > 100:
            logger.warn("obtener_datos_de_contactos(): de id_contactos "
                "contiene muchos elementos, exactamente %s", len(id_contactos))
        with log_timing(logger, "obtener_datos_de_contactos() tardo %s seg"):
            # forzamos query
            values = list(Contacto.objects.filter(
                id__in=id_contactos).values_list('id', 'telefono'))

        return values

    def obtener_ts_ultimo_evento_de_campana(self, id_campana):
        """Devuelve el timestamp del ultimo evento registrado
        para la campaña
        """
        value = self.filter(campana_id=id_campana).aggregate(Max('timestamp'))
        return value['timestamp__max']


class EventoDeContacto(models.Model):
    """
    - http://www.voip-info.org/wiki/view/Asterisk+cmd+Dial
    - http://www.voip-info.org/wiki/view/Asterisk+variable+DIALSTATUS
    """

    objects = EventoDeContactoManager()
    objects_gestion_llamadas = GestionDeLlamadasManager()
    objects_simulacion = SimuladorEventoDeContactoManager()
    objects_estadisticas = EventoDeContactoEstadisticasManager()

    EVENTO_CONTACTO_PROGRAMADO = 1
    """El contacto asociado al evento ha sido programado, o sea,
    eventualmente se generará una llamada al contacto en cuestión.

    Todos los contactos que sólo poseen un evento de este tipo
    son contactos que nunca fueron procesados por el daemon, ni una vez.

    *Este evento es registrado por el daemon que realiza las llamadas.*
    """

    EVENTO_DAEMON_INICIA_INTENTO = 2
    """EL intento ha sido tomado por Daemon para ser procesado.
    Este evento *NO* implica que se haya realizado la llamada, pero
    *SI* que se ha tomado el contacto (asociado a este eveto)
    para intentar ser procesado. Representa un *INTENTO* de llamado.

    *Este evento es registrado por el daemon que realiza las llamadas.*
    """

    EVENTO_DAEMON_ORIGINATE_SUCCESSFUL = 11
    """El originate se produjo exitosamente.

    *Este evento es registrado por el daemon que realiza las llamadas.*
    """

    EVENTO_DAEMON_ORIGINATE_FAILED = 12
    """El comando ORIGINATE se ejecutó, pero devolvio error.

    *Este evento es registrado por el daemon que realiza las llamadas.*
    """

    EVENTO_DAEMON_ORIGINATE_INTERNAL_ERROR = 13
    """El originate no se pudo realizar por algun problema
    interno (ej: Asterisk caido, problema de login, etc.)
    Este tipo de error implica que el ORIGINATE seguramente no
    ha llegado al Asterisk.

    *Este evento es registrado por el daemon que realiza las llamadas.*
    """

    EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO = 21
    """Este evento indica que Asterisk ha inicio del proceso de la llamada,
    en en LOCAL CHANNEL (ej: en el contexto '[FTS_local_campana_NNN]').

    *Este evento es registrado via el proxy AGI.*
    """

    EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO = 22
    """Asterisk delegó control al context de la campaña.
    Este evento indica que Asterisk ha inicio del proceso REAL de la llamada,
    en el contexto asociado a la campaña (ej: en el contexto '[campania_NNN]').

    Asterisk "conecta" con el contex "[campania_NNN]" cuando el destinatario
    ha atendido. Por lo tanto, la existencia de este evento asociado a una
    llamada, implica que el destinatario ha contestado.

    *Este evento es registrado via el proxy AGI.*
    """

    EVENTO_ASTERISK_DIALPLAN_CAMPANA_FINALIZADO = 23
    """Asterisk llego al final del context de la campana.

    *Este evento es registrado via el proxy AGI.*
    """

    EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_T = 24
    """Asterisk llego al final del context de la campana,
    pero como un error (exten t).

    *Este evento es registrado via el proxy AGI.*
    """

    EVENTO_ASTERISK_DIALPLAN_CAMPANA_ERR_I = 25
    """Asterisk llego al final del context de la campana,
    pero como un error (exten i).

    *Este evento es registrado via el proxy AGI.*
    """

    EVENTO_ASTERISK_DIALSTATUS_ANSWER = 31
    """Dial() - DIALSTATUS: ANSWER"""

    EVENTO_ASTERISK_DIALSTATUS_BUSY = 32
    """Dial() - DIALSTATUS: BUSY"""

    EVENTO_ASTERISK_DIALSTATUS_NOANSWER = 33
    """Dial() - DIALSTATUS: NOANSWER"""

    EVENTO_ASTERISK_DIALSTATUS_CANCEL = 34
    """Dial() - DIALSTATUS: CANCEL"""

    EVENTO_ASTERISK_DIALSTATUS_CONGESTION = 35
    """Dial() - DIALSTATUS: CONGESTION"""

    EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL = 36
    """Dial() - DIALSTATUS: CHANUNAVAIL"""

    EVENTO_ASTERISK_DIALSTATUS_DONTCALL = 37
    """Dial() - DIALSTATUS: DONTCALL"""

    EVENTO_ASTERISK_DIALSTATUS_TORTURE = 38
    """Dial() - DIALSTATUS: TORTURE"""

    EVENTO_ASTERISK_DIALSTATUS_INVALIDARGS = 39
    """Dial() - DIALSTATUS: INVALIDARGS"""

    EVENTO_ASTERISK_DIALSTATUS_UNKNOWN = 40
    """Dial() - El valor de DIALSTATUS recibido por el sistema
    no es ninguno de los reconocidos por el sistema
    """

    EVENTO_ASTERISK_OPCION_0 = 50
    """El usuario ha seleccionado una opción 0 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_1 = 51
    """El usuario ha seleccionado una opción 1 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_2 = 52
    """El usuario ha seleccionado una opción 2 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_3 = 53
    """El usuario ha seleccionado una opción 3 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_4 = 54
    """El usuario ha seleccionado una opción 4 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_5 = 55
    """El usuario ha seleccionado una opción 5 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_6 = 56
    """El usuario ha seleccionado una opción 6 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_7 = 57
    """El usuario ha seleccionado una opción 7 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_8 = 58
    """El usuario ha seleccionado una opción 8 utilizando utilizando
    el teclado numerico.
    """

    EVENTO_ASTERISK_OPCION_9 = 59
    """El usuario ha seleccionado una opción 9 utilizando utilizando
    el teclado numerico.
    """

    NUMERO_OPCION_MAP = {
        0: EVENTO_ASTERISK_OPCION_0,
        1: EVENTO_ASTERISK_OPCION_1,
        2: EVENTO_ASTERISK_OPCION_2,
        3: EVENTO_ASTERISK_OPCION_3,
        4: EVENTO_ASTERISK_OPCION_4,
        5: EVENTO_ASTERISK_OPCION_5,
        6: EVENTO_ASTERISK_OPCION_6,
        7: EVENTO_ASTERISK_OPCION_7,
        8: EVENTO_ASTERISK_OPCION_8,
        9: EVENTO_ASTERISK_OPCION_9,
    }
    """Mapea ENTERO (numero de opcion) a EVENTO_ASTERISK_OPCION_9"""

    EVENTO_A_NUMERO_OPCION_MAP = dict([
       (v, k) for k, v in NUMERO_OPCION_MAP.iteritems()])
    """Mapea EVENTO_ASTERISK_OPCION_9 a ENTERO (numero de opcion)"""

    DIALSTATUS_MAP = {
        'ANSWER': EVENTO_ASTERISK_DIALSTATUS_ANSWER,
        'BUSY': EVENTO_ASTERISK_DIALSTATUS_BUSY,
        'NOANSWER': EVENTO_ASTERISK_DIALSTATUS_NOANSWER,
        'CANCEL': EVENTO_ASTERISK_DIALSTATUS_CANCEL,
        'CONGESTION': EVENTO_ASTERISK_DIALSTATUS_CONGESTION,
        'CHANUNAVAIL': EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL,
        'DONTCALL': EVENTO_ASTERISK_DIALSTATUS_DONTCALL,
        'TORTURE': EVENTO_ASTERISK_DIALSTATUS_TORTURE,
        'INVALIDARGS': EVENTO_ASTERISK_DIALSTATUS_INVALIDARGS,
    }

    campana_id = models.IntegerField(db_index=True)
    contacto_id = models.IntegerField(db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    evento = models.SmallIntegerField(db_index=True)
    dato = models.SmallIntegerField(db_index=True)
    """Aunque se llama `dato`, aqui guardamos el nro de intento
    al que corresponde este evento.

    Para el evento EVENTO_CONTACTO_PROGRAMADO, utilizamos `dato == 0`.

    Por lo tanto, cuando `dato == 1`, implica que se trata de un evento
    asociado al 1er intento.
    """

    def __unicode__(self):
        return "EventoDeContacto-{0}-{1}".format(
            self.campana_id, self.contacto_id)
