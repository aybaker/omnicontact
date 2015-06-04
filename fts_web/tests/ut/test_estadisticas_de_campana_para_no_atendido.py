# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import connection
from fts_web.services.estadisticas_campana import (
    EstadisticasCampanaService)
from fts_daemon.models import EventoDeContacto
from fts_web.tests.utiles import FTSenderBaseTest


class EstadisticasParaReporteNoAtendido(FTSenderBaseTest):
    """
    Este unit test testa todo los metodos y/o servicios, relacionado con la
    obtención de información para los reportes de no atendidos
    """

    def test_obtener_total_no_atendido_por_evento_un_intento(self):
        """
        Este test chequea que se generen correctamente los datos de no 
        atendidos por los 4 diferentes estados:Ocupado, No atendido, Canal no 
        disponible y congestion
        """
        campana = self.crear_campana_finalizada()

        self._crear_tabla_evento_depurado(campana)

        # crear evento programado
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)

        # inicia intento
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)

        # originate exitoso
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)

        # canal local iniciado
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)

        # atendieron
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_ASTERISK_OPCION_1, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_ASTERISK_OPCION_2, 1)

        # no atendieron
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION, 1)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER, 1)

        lista_eventos = [EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY,
                         EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL]

        # obtenemos el listado de los eventos
        listado = EventoDeContacto.objects_estadisticas.\
            obtener_eventos_por_contacto(campana)

        estadisticas_para_reporte_no_atendido = EstadisticasCampanaService()

        counter_por_evento = estadisticas_para_reporte_no_atendido.\
            _obtener_total_no_atendidos_por_evento(listado)
        self.assertEqual(lista_eventos, counter_por_evento.keys())
        self.assertDictEqual(counter_por_evento,
            {EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY: 0,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER: 1,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION: 1,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL: 0})

    def test_obtener_total_no_atendido_por_evento_dos_intento(self):
        """
        Este test chequea que se generen correctamente los datos de no 
        atendidos por los 4 diferentes estados:Ocupado, No atendido, Canal no 
        disponible y congestion
        """
        campana = self.crear_campana_finalizada()

        self._crear_tabla_evento_depurado(campana)

        # crear evento programado
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)

        # inicia intento 1
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)

        # originate exitoso
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)

        # canal local iniciado
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)

        # atendieron
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento(campana, 1, EventoDeContacto.EVENTO_ASTERISK_OPCION_1, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento(campana, 3, EventoDeContacto.EVENTO_ASTERISK_OPCION_2, 1)

        # no atendieron
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION, 1)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER, 1)

        # inicia intento 2
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)

        # originate exitoso
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)

        # canal local iniciado        
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)

        # atendieron
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 2)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 2)
        self._insertar_evento(campana, 4, EventoDeContacto.EVENTO_ASTERISK_OPCION_1, 2)

        # no atendieron
        self._insertar_evento(campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY, 2)




        lista_eventos = [EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY,
                         EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL]

        # obtenemos el listado de los eventos
        listado = EventoDeContacto.objects_estadisticas.\
            obtener_eventos_por_contacto(campana)

        print listado

        estadisticas_para_reporte_no_atendido = EstadisticasCampanaService()

        counter_por_evento = estadisticas_para_reporte_no_atendido.\
            _obtener_total_no_atendidos_por_evento(listado)
        print counter_por_evento
        self.assertEqual(lista_eventos, counter_por_evento.keys())
        self.assertDictEqual(counter_por_evento,
            {EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY: 1,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER: 0,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION: 0,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL: 0})

    def _crear_tabla_evento_depurado(self, campana):
        nombre_tabla = "EDC_depurados_{0}".format(campana.pk)

        cursor = connection.cursor()
        sql = """CREATE TABLE {0} AS
            SELECT * FROM fts_daemon_eventodecontacto
            WHERE campana_id = %s
            WITH DATA
        """.format(nombre_tabla)

        params = [campana.id]
        cursor.execute(sql, params)

    def _insertar_evento(self, campana, contacto_id, evento, intento=0):
        """
        Realiza las inserciones de los eventos en la tabla EDC_depurados_{0} 
        de la campana pasada por parametro
        """
        nombre_tabla = "EDC_depurados_{0}".format(campana.pk)

        cursor = connection.cursor()
        sql = """INSERT INTO {0}
        (campana_id, contacto_id, timestamp, evento, dato)
        VALUES(%(campana_id)s, %(contacto_id)s, NOW(), %(evento)s,
        %(intento)s)
        """.format(nombre_tabla)

        params = {
            'campana_id': campana.id,
            'contacto_id': contacto_id,
            'evento': evento,
            'intento': intento,
        }
        cursor.execute(sql, params)