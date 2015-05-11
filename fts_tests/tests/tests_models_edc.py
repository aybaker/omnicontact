# -*- coding: utf-8 -*-

"""Tests generales"""
from __future__ import unicode_literals

import logging
import random

from django.test.utils import override_settings
from django.utils.unittest.case import skipUnless
from fts_daemon.models import EventoDeContacto
from fts_tests.tests.utiles import EventoDeContactoAssertUtilesMixin
from fts_web.models import BaseDatosContacto
from fts_web.tests.utiles import FTSenderBaseTest, \
    default_db_is_postgresql


#from django.conf import settings
logger = logging.getLogger(__name__)

CONT_PROG = EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO
D_INI_INT = EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO
D_ORIG_SUC = EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL
D_ORIG_FAIL = EventoDeContacto.EVENTO_DAEMON_ORIGINATE_FAILED
D_ORIG_INT_ERR = EventoDeContacto.EVENTO_DAEMON_ORIGINATE_INTERNAL_ERROR

A_DIALP_INI = EventoDeContacto.EVENTO_ASTERISK_DIALPLAN_CAMPANA_INICIADO
A_OPC_0 = EventoDeContacto.EVENTO_ASTERISK_OPCION_0
A_OPC_7 = EventoDeContacto.EVENTO_ASTERISK_OPCION_7
A_OPC_2 = EventoDeContacto.EVENTO_ASTERISK_OPCION_2


class WorkflowEventoDeContactoTests(FTSenderBaseTest,
    EventoDeContactoAssertUtilesMixin):
    """Clase para testear EventoDeContacto y EventoDeContactoManager"""

    @skipUnless(default_db_is_postgresql(), "Requiere PostgreSql")
    def _run_workflow_contactos(self):
        """Testea metodos relacionados con workflow de proceso de
        contactos:

        - EDC.obtener_pendientes()
        - EDC.programar_campana()
        """
        TAM_CAMPANA = cant_pendientes = 97
        EV_FINALIZADOR = EventoDeContacto.objects.\
            get_eventos_finalizadores()[0]

        logger.info("Iniciando test_workflow_contactos()")

        #======================================================================
        # Crea campanas
        #======================================================================
        campana, _ = self._crear_campanas_y_bds(TAM_CAMPANA)

        # No deberia haber eventos
        self._assertCountEventos(campana)

        # Chequeamos `obtener_array_eventos_por_contacto()`
        self._assertArrayEventos(campana)

        # Chequeamos `obtener_estadisticas_de_campana()`
        counter_x_estado, counter_intentos, counter_por_evento = \
            EventoDeContacto.objects_estadisticas.\
                obtener_estadisticas_de_campana(campana.id)
        self.assertDictEqual(counter_x_estado,
            {'finalizado_x_evento_finalizador': 0,
                'finalizado_x_limite_intentos': 0,
                'no_selecciono_opcion': 0,
                'pendientes': 0})
        self.assertDictEqual(counter_intentos, {})
        # TODO: counter_por_evento y _assertCountEventos(): ambos
        #  deberia ser contar la misma cant. de eventos

        # No deberia haber informacion de intentos
        self._assertCountIntentos(campana)

        #======================================================================
        # Activamos campana
        #======================================================================
        campana.activar()

        # Solo deberia haber eventos del tipo CONT_PROG
        self._assertCountEventos(campana, CONT_PROG)

        # Chequeamos `obtener_array_eventos_por_contacto()`
        self._assertArrayEventos(campana, CONT_PROG)

        # Chequeamos `obtener_estadisticas_de_campana()`
        counter_x_estado, counter_intentos, counter_por_evento = \
            EventoDeContacto.objects_estadisticas.\
                obtener_estadisticas_de_campana(campana.id)
        self.assertDictEqual(counter_x_estado,
            {'finalizado_x_evento_finalizador': 0,
                'finalizado_x_limite_intentos': 0,
                'no_selecciono_opcion': 0,
                'pendientes': TAM_CAMPANA})
        self.assertDictEqual(counter_intentos, {0: TAM_CAMPANA})
        # TODO: counter_por_evento y _assertCountEventos(): ambos
        #  deberia ser contar la misma cant. de eventos

        # obtener_pendientes() deberia devolver pendientes, todos en 0
        self._assertPendientes(campana, cant_pendientes, 0)

        # No deberia haber informacion de intentos
        self._assertCountIntentos(campana)

        #======================================================================
        # Simulamos 1er intento de algunas llamadas y chequeamos intentos
        #======================================================================
        with override_settings(DEBUG=True):
            EventoDeContacto.objects_simulacion.\
                simular_realizacion_de_intentos(campana.id, intento=1)

        # Chequeamos `obtener_count_eventos()`
        self._assertCountEventos(campana, CONT_PROG, D_INI_INT)

        # Chequeamos `obtener_array_eventos_por_contacto()`
        self._assertArrayEventos(campana, CONT_PROG, D_INI_INT)

        # Chequeamos `obtener_estadisticas_de_campana()`
        counter_x_estado, counter_intentos, counter_por_evento = \
            EventoDeContacto.objects_estadisticas.\
                obtener_estadisticas_de_campana(campana.id)
        self.assertDictEqual(counter_x_estado,
            {'finalizado_x_evento_finalizador': 0,
                'finalizado_x_limite_intentos': 0,
                'no_selecciono_opcion': 0,
                'pendientes': TAM_CAMPANA})
        self.assertEquals(len(counter_intentos), 2)
        self.assertIn(0, counter_intentos)
        self.assertIn(1, counter_intentos)
        # TODO: counter_por_evento y _assertCountEventos(): ambos
        #  deberia ser contar la misma cant. de eventos

        # Chequeamos q' no haya intentos registrados
        self._assertCountIntentos(campana, 1)

        # Chequeamos `obtener_pendientes()`
        self._assertPendientes(campana, cant_pendientes, 0, 1)

        #======================================================================
        # Simulamos finalizacion de algunos contactos
        #======================================================================

        count_eventos_pre = self._assertCountEventos(campana, CONT_PROG,
            D_INI_INT)
        self.assertFalse(EV_FINALIZADOR in count_eventos_pre)

        EventoDeContacto.objects_simulacion.simular_evento(campana.id, 1,
            EV_FINALIZADOR, 0.2)

        count_eventos_post = self._assertCountEventos(campana, CONT_PROG,
            D_INI_INT, EV_FINALIZADOR)

        cantidad_finalizados = count_eventos_post[EV_FINALIZADOR]
        self.assertTrue(cantidad_finalizados > 0)
        self.assertTrue(cantidad_finalizados < TAM_CAMPANA)
        cant_pendientes = cant_pendientes - cantidad_finalizados

        # Chequeamos `obtener_estadisticas_de_campana()`
        counter_x_estado, counter_intentos, counter_por_evento = \
            EventoDeContacto.objects_estadisticas.\
                obtener_estadisticas_de_campana(campana.id)
        import pprint
        pprint.pprint(counter_x_estado)
        self.assertDictEqual(counter_x_estado,
            {'finalizado_x_evento_finalizador': cantidad_finalizados,
                'finalizado_x_limite_intentos': 0,
                'no_selecciono_opcion': cantidad_finalizados,
                'pendientes': TAM_CAMPANA - cantidad_finalizados})
        self.assertEquals(len(counter_intentos), 2)
        self.assertIn(0, counter_intentos)
        self.assertIn(1, counter_intentos)
        # TODO: counter_por_evento y _assertCountEventos(): ambos
        #  deberia ser contar la misma cant. de eventos

        #======================================================================
        # Simulamos 2do intento de algunas llamadas, otra vez
        #======================================================================
        with override_settings(DEBUG=True):
            EventoDeContacto.objects_simulacion.\
                simular_realizacion_de_intentos(campana.id, intento=2)

        # Chequeamos q' no haya intentos registrados
        self._assertCountIntentos(campana, 1, 2)

        # Chequeamos `obtener_pendientes()`
        self._assertPendientes(campana, cant_pendientes, 0, 1, 2)

        # Chequeamos `obtener_estadisticas_de_campana()`
        counter_x_estado, counter_intentos, counter_por_evento = \
            EventoDeContacto.objects_estadisticas.\
                obtener_estadisticas_de_campana(campana.id)
        self.assertDictEqual(counter_x_estado,
            {'finalizado_x_evento_finalizador': cantidad_finalizados,
                'finalizado_x_limite_intentos': 0,
                'no_selecciono_opcion': cantidad_finalizados,
                'pendientes': TAM_CAMPANA - cantidad_finalizados})
        self.assertEquals(len(counter_intentos), 3)
        self.assertIn(0, counter_intentos)
        self.assertIn(1, counter_intentos)
        self.assertIn(2, counter_intentos)
        # TODO: counter_por_evento y _assertCountEventos(): ambos
        #  deberia ser contar la misma cant. de eventos

        #======================================================================
        # Simulamos 3er intento de algunas llamadas, otra vez
        #======================================================================
        # Nos aseguramos q' se generen intentos para todos los contactos
        with override_settings(DEBUG=True):
            EventoDeContacto.objects_simulacion.\
                simular_realizacion_de_intentos(campana.id, probabilidad=1.1,
                    intento=3)

        # Chequeamos `obtener_pendientes()`
        pendientes_1_y_2_intentos = self._assertPendientes(campana, None, 1, 2)
        self.assertTrue(len(pendientes_1_y_2_intentos) < TAM_CAMPANA)

        # Esta vez DEBERIA haber contactos finalizados x limite de intentos!
        # Chequeamos `obtener_estadisticas_de_campana()`
        counter_x_estado, counter_intentos, counter_por_evento = \
            EventoDeContacto.objects_estadisticas.\
                obtener_estadisticas_de_campana(campana.id)

        self.assertEquals(len(counter_intentos), 3)
        self.assertNotIn(0, counter_intentos)
        self.assertIn(1, counter_intentos)
        self.assertIn(2, counter_intentos)
        self.assertIn(3, counter_intentos)

        self.assertTrue(counter_x_estado['finalizado_x_limite_intentos'] > 0)
        self.assertTrue(counter_x_estado['finalizado_x_limite_intentos']
            <= counter_intentos[3])
        # TODO: counter_por_evento y _assertCountEventos(): ambos
        #  deberia ser contar la misma cant. de eventos

        #======================================================================
        # Simulamos 4to intento de algunas llamadas, otra vez ~~~~~
        #======================================================================
        # Nos aseguramos q' se generen intentos para todos los contactos
        with override_settings(DEBUG=True):
            EventoDeContacto.objects_simulacion.\
                simular_realizacion_de_intentos(campana.id, probabilidad=1.1,
                    intento=4)

        # Chequeamos `obtener_pendientes()`
        pendientes_2 = self._assertPendientes(campana, None, 2)
        self.assertTrue(len(pendientes_2) < TAM_CAMPANA)
        self.assertTrue(len(pendientes_1_y_2_intentos) > len(pendientes_2))

        #======================================================================
        # Simulamos 5to intento de algunas llamadas, otra vez ~~~~~
        #======================================================================
        # Nos aseguramos q' se generen intentos para todos los contactos
        with override_settings(DEBUG=True):
            EventoDeContacto.objects_simulacion.\
                simular_realizacion_de_intentos(campana.id, probabilidad=1.1,
                    intento=5)

        # Ya no deberia devolver pendientes!
        # Chequeamos `obtener_pendientes()`
        self._assertPendientes(campana, 0)

    def test_obtener_pendientes_no_en_curso(self):

        campana, _ = self._crear_campanas_y_bds(10)
        campana.activar()

        pendientes = EventoDeContacto.objects_gestion_llamadas.\
            obtener_pendientes(campana.id)

        self.assertEquals(len(pendientes), 10)

        id_contactos_en_curso = []
        for contacto_pendiente in pendientes:
            # Agregamos contacto a lista de 'en curso'
            id_contactos_en_curso.append(contacto_pendiente.id_contacto)

            # Llamamos a obtener_pendientes_no_en_curso()
            pendientes_sin_en_curso = EventoDeContacto.\
                objects_gestion_llamadas.\
                obtener_pendientes_no_en_curso(campana.id,
                    contacto_ids_en_curso=id_contactos_en_curso)

            self.assertEquals(len(pendientes_sin_en_curso),
                              10 - len(id_contactos_en_curso))

            self.assertNotIn(contacto_pendiente.id_contacto,
                             [cp_sin_en_curso.id_contacto
                              for cp_sin_en_curso in pendientes_sin_en_curso])

    #--------------------------------------------------------------------------
    # Punto de entrada al test, acomoda settings antes de ejecutar test real
    #--------------------------------------------------------------------------

    @skipUnless(default_db_is_postgresql(), "Requiere PostgreSql")
    def test_programar_campana_postgresl(self):
        with override_settings(
            FTS_PROGRAMAR_CAMPANA_FUNC="_programar_campana_postgresql"):
            self._run_workflow_contactos()

    #--------------------------------------------------------------------------
    # Metodos utilitarios
    #--------------------------------------------------------------------------

    def _get_logger(self):
        return logger

    def _crear_campanas_y_bds(self, cant_contactos):
        """Crear 3 campanas activas, y devuelve una de ellas"""
        with override_settings(DEBUG=True):
            self.assertEquals(BaseDatosContacto.objects.count(), 0)
            bd1 = EventoDeContacto.objects_simulacion.\
                crear_bd_contactos_con_datos_random(91)
            bd2 = EventoDeContacto.objects_simulacion.\
                crear_bd_contactos_con_datos_random(cant_contactos)
            bd3 = EventoDeContacto.objects_simulacion.\
                crear_bd_contactos_con_datos_random(82)

            self.assertEquals(bd2.contactos.count(), cant_contactos)

        # Creamos 2 campanas (activas), pero la que vamos a devolver,
        #  NO la queremos activa...
        self.assertEqual(EventoDeContacto.objects.all().count(), 0)
        _ = self.crear_campana_activa(bd_contactos=bd1)
        c2 = self.crear_campana(bd_contactos=bd2,
            cantidad_intentos=3)
        _ = self.crear_campana_activa(bd_contactos=bd3)

        self.assertEqual(EventoDeContacto.objects.all().count(), 91 + 82)

        return c2, bd2


class OpcionesTests(FTSenderBaseTest,
    EventoDeContactoAssertUtilesMixin):
    """Clase para testear manejo de eventos de opciones"""

    def test_opciones(self):
        campana = self.crear_campana_activa(cant_contactos=19)
        contactos = list(campana.bd_contacto.contactos.all())
        random.shuffle(contactos)

        contacto_id = contactos.pop().id
        EventoDeContacto.objects.dialplan_campana_iniciado(
            campana.id, contacto_id, 1)
        EventoDeContacto.objects.inicia_intento(campana.id, contacto_id, 1)
        self._assertCountEventos(campana, CONT_PROG, A_DIALP_INI, D_INI_INT)

        contacto_id = contactos.pop().id
        EventoDeContacto.objects.dialplan_campana_iniciado(
            campana.id, contacto_id, 1)
        EventoDeContacto.objects.opcion_seleccionada(
            campana.id, contacto_id, 1, A_OPC_0)
        self._assertCountEventos(campana, CONT_PROG, A_DIALP_INI, D_INI_INT,
            A_OPC_0)

        contacto_id = contactos.pop().id
        EventoDeContacto.objects.dialplan_campana_iniciado(
            campana.id, contacto_id, 1)
        EventoDeContacto.objects.opcion_seleccionada(
            campana.id, contacto_id, 1, A_OPC_7)
        self._assertCountEventos(campana, CONT_PROG, A_DIALP_INI, D_INI_INT,
            A_OPC_0, A_OPC_7)

        contacto_id = contactos.pop().id
        EventoDeContacto.objects.dialplan_campana_iniciado(
            campana.id, contacto_id, 1)
        EventoDeContacto.objects.opcion_seleccionada(
            campana.id, contacto_id, 1, A_OPC_2)
        self._assertCountEventos(campana, CONT_PROG, A_DIALP_INI, D_INI_INT,
            A_OPC_0, A_OPC_7, A_OPC_2)

    def _get_logger(self):
        return logger
