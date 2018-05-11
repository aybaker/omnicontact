# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from fts_web.services.estadisticas_campana import (
    EstadisticasCampanaService)
from fts_daemon.models import EventoDeContacto
from fts_web.tests.utiles import FTSenderBaseTest


class EstadisticasParaReporteNoAtendido(FTSenderBaseTest):
    """
    Este unit test testa todo los metodos y/o servicios, relacionado con la
    obtención de información para los reportes de no atendidos
    """
    def setUp(self):
        self.campana = self.crear_campana_finalizada()
        self.campana.depurar()
        self._crear_tabla_de_edc_depurados(self.campana)

    def test_obtener_total_no_atendido_por_evento_un_intento(self):
        """
        Este test chequea que se generen correctamente los datos de no
        atendidos por los 4 diferentes estados:Ocupado, No atendido, Canal no
        disponible y congestion
        """

        # crear evento programado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)

        # inicia intento
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)

        # originate exitoso
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)

        # canal local iniciado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)

        # atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_OPCION_1, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_OPCION_2, 1)

        # no atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER, 1)

        lista_eventos = [EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY,
                         EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL]

        # obtenemos el listado de los eventos
        listado = EventoDeContacto.objects_estadisticas.\
            obtener_eventos_por_contacto(self.campana)

        estadisticas_para_reporte_no_atendido = EstadisticasCampanaService()

        counter_por_evento = estadisticas_para_reporte_no_atendido.\
            _obtener_total_no_atendidos_por_evento(listado)
        self.assertEqual(lista_eventos, counter_por_evento.keys())
        self.assertDictEqual(counter_por_evento,
            {EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY: 0,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER: 1,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION: 1,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL: 0})

    def test_obtener_total_no_atendido_por_evento_dos_intento_busy(self):
        """
        Este test chequea que se generen correctamente los datos de no
        atendidos por los 4 diferentes estados:Ocupado, No atendido, Canal no
        disponible y congestion
        """

        # crear evento programado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)

        # inicia intento 1
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)

        # originate exitoso
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)

        # canal local iniciado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)

        # atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_OPCION_1, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_OPCION_2, 1)

        # no atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER, 1)

        # inicia intento 2
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)

        # originate exitoso
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)

        # canal local iniciado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)

        # atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_OPCION_1, 2)

        # no atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY, 2)

        lista_eventos = [EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY,
                         EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL]

        # obtenemos el listado de los eventos
        listado = EventoDeContacto.objects_estadisticas.\
            obtener_eventos_por_contacto(self.campana)

        estadisticas_para_reporte_no_atendido = EstadisticasCampanaService()

        counter_por_evento = estadisticas_para_reporte_no_atendido.\
            _obtener_total_no_atendidos_por_evento(listado)

        self.assertEqual(lista_eventos, counter_por_evento.keys())
        self.assertDictEqual(counter_por_evento,
            {EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY: 1,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER: 0,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION: 0,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL: 0})

    def test_obtener_total_no_atendido_por_evento_dos_intento_no_answer(self):
        """
        Este test chequea que se generen correctamente los datos de no
        atendidos por los 4 diferentes estados:Ocupado, No atendido, Canal no
        disponible y congestion
        """

        # crear evento programado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)

        # inicia intento 1
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)

        # originate exitoso
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)

        # canal local iniciado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)

        # atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_OPCION_1, 1)

        # no atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER, 1)

        # inicia intento 2
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)

        # originate exitoso
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)

        # canal local iniciado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)

        # atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_OPCION_2, 2)

        # no atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION, 2)

        lista_eventos = [EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY,
                         EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL]

        # obtenemos el listado de los eventos
        listado = EventoDeContacto.objects_estadisticas.\
            obtener_eventos_por_contacto(self.campana)

        estadisticas_para_reporte_no_atendido = EstadisticasCampanaService()

        counter_por_evento = estadisticas_para_reporte_no_atendido.\
            _obtener_total_no_atendidos_por_evento(listado)

        self.assertEqual(lista_eventos, counter_por_evento.keys())
        self.assertDictEqual(counter_por_evento,
            {EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY: 0,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER: 2,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION: 0,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL: 0})

    def test_obtener_total_no_atendido_por_evento_dos_intento_failed(self):
        """
        Este test chequea que se generen correctamente los datos de no
        atendidos por los 4 diferentes estados:Ocupado, No atendido, Canal no
        disponible y congestion
        """

        # crear evento programado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)

        # inicia intento 1
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)

        # originate exitoso
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)

        # canal local iniciado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)

        # atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_OPCION_1, 1)

        # no atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL, 1)

        # inicia intento 2
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)

        # originate exitoso
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)

        # canal local iniciado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)

        # atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_OPCION_2, 2)

        # no atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION, 2)

        lista_eventos = [EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY,
                         EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION,
            EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL]

        # obtenemos el listado de los eventos
        listado = EventoDeContacto.objects_estadisticas.\
            obtener_eventos_por_contacto(self.campana)

        estadisticas_para_reporte_no_atendido = EstadisticasCampanaService()

        counter_por_evento = estadisticas_para_reporte_no_atendido.\
            _obtener_total_no_atendidos_por_evento(listado)

        self.assertEqual(lista_eventos, counter_por_evento.keys())
        self.assertDictEqual(counter_por_evento,
            {EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY: 0,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER: 0,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION: 1,
                EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL: 1})
