# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from fts_web.services.estadisticas_campana import (
    EstadisticasCampanaService)
from fts_daemon.models import EventoDeContacto
from fts_web.tests.utiles import FTSenderBaseTest


class EstadisticasParaReporteAtendido(FTSenderBaseTest):
    """
    Este unit test testa todo los metodos y/o servicios, relacionado con la
    obtención de información para los reportes de atendidos
    """
    def setUp(self):
        self.campana = self.crear_campana_finalizada()
        self.campana.depurar()
        self._crear_tabla_y_depurar_eventos(self.campana)

    def test_obtener_total_atendido_por_evento_un_intento(self):
        """
        Este test chequea que se generen correctamente los datos de atendidos
        por los 2 eventos:Humano y contestador con un intento de llamada
        """

        # crear evento programado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)

        # inicia intento
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)

        # originate exitoso
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)

        # canal local iniciado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)

        # atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_OPCION_1, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_OPCION_2, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_ASTERISK_OPCION_2, 1)

        # no atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CONGESTION, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_NOANSWER, 1)

        lista_eventos = [EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED,
                         EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED]

        # obtenemos el listado de los eventos
        listado = EventoDeContacto.objects_estadisticas.\
            obtener_eventos_por_contacto(self.campana)

        estadisticas_para_reporte_atendido = EstadisticasCampanaService()

        counter_por_evento = estadisticas_para_reporte_atendido.\
            _obtener_totales_atendidos_por_evento_amd(listado)
        self.assertEqual(lista_eventos, counter_por_evento.keys())
        self.assertDictEqual(counter_por_evento,
            {EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED: 3,
                EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED: 1})

    def test_obtener_total_atendido_por_evento_dos_intento(self):
        """
        Este test chequea que se generen correctamente los datos de atendidos
        por los 2 eventos:Humano y contestador con dos intentos de llamada
        """

        # crear evento programado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO)

        # inicia intento 1
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 1)

        # originate exitoso
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 1)

        # canal local iniciado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 1, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 3, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 1)

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
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY, 1)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_CHANUNAVAIL, 1)

        # inicia intento 2
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO, 2)

        # originate exitoso
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL, 2)

        # canal local iniciado
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_LOCAL_CHANNEL_INICIADO, 2)

        # atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 4, EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 5, EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO, 2)
        self._insertar_evento_en_tabla_de_depurados(self.campana, 6, EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED, 2)

        # no atendieron
        self._insertar_evento_en_tabla_de_depurados(self.campana, 2, EventoDeContacto.EVENTO_ASTERISK_DIALSTATUS_BUSY, 2)

        lista_eventos = [EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED,
                         EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED]

        # obtenemos el listado de los eventos
        listado = EventoDeContacto.objects_estadisticas.\
            obtener_eventos_por_contacto(self.campana)

        estadisticas_para_reporte_atendido = EstadisticasCampanaService()

        counter_por_evento = estadisticas_para_reporte_atendido.\
            _obtener_totales_atendidos_por_evento_amd(listado)
        self.assertEqual(lista_eventos, counter_por_evento.keys())
        self.assertDictEqual(counter_por_evento,
            {EventoDeContacto.EVENTO_ASTERISK_AMD_HUMAN_DETECTED: 2,
                EventoDeContacto.EVENTO_ASTERISK_AMD_MACHINE_DETECTED: 3})
