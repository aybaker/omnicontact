# -*- coding: utf-8 -*-

"""Tests del componente scheduler / RRT"""

from __future__ import unicode_literals

import time

from django.test.testcases import LiveServerTestCase
from django.test.utils import override_settings
from fts_daemon.poll_daemon.call_status import NoHayCampanaEnEjecucion, \
    CampanaCallStatus
from fts_daemon.poll_daemon.campana_tracker import \
    LimiteDeCanalesAlcanzadoError
from fts_tests.tests.tests_poll_daemon_campana_tracker import \
    PollDaemonTestUtilsMixin
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging


logger = _logging.getLogger(__name__)


class CampanaCallStatusBaneoUT(LiveServerTestCase, FTSenderBaseTest,
    PollDaemonTestUtilsMixin):

    def test_banear_campana_banea_campana(self):
        # FIXME: implementar
        pass

    def test_obtener_baneados_por_razon_devuelve_correctos(self):
        # FIXME: implementar
        pass


class DecisionDeRefrescarONoUT(LiveServerTestCase, FTSenderBaseTest,
    PollDaemonTestUtilsMixin):

    def test_necesita_refrescar_trackers_devuelve_valor_correcto(self):

        class CampanaCallStatusTmp(CampanaCallStatus):
            def _obtener_campanas_en_ejecucion(self):
                return []

            def _get_tiempo_minimo_entre_refresco(self):
                return 0.1

        ccs = CampanaCallStatusTmp()

        # -----

        # llamada inicial deberia devolver True
        self.assertTrue(ccs._necesita_refrescar_trackers())

        # luego de actualizar, devuelve False (el assert puede fallar
        # en equipos lentos, si se vence muy rapido
        with self.assertRaises(NoHayCampanaEnEjecucion):
            ccs.refrescar_trackers()
        self.assertFalse(ccs._necesita_refrescar_trackers())

        # Durante unos momentos deberia devolver false, y luego,
        # True
        count = 0
        while not ccs._necesita_refrescar_trackers():
            # esperamos hasta q' se venza
            self.assertTrue(count < 11)
            count += 1
            time.sleep(0.01)


class RefrescaTrackersUT(LiveServerTestCase, FTSenderBaseTest,
    PollDaemonTestUtilsMixin):

    def test__refrescar_trackers__agrega_nuevos_trackers(self):
        """Testea q' se crean trackers para nuevas campanas,
        y quedan en estado "activa"
        """
        campana1 = self._crear_1_campana()
        ccs = CampanaCallStatus()
        self.assertEquals(len(ccs._trackers_campana_dict), 0)

        # -----

        # Chequeamos q' agregue cuando no hay trackers pre-existentes
        ccs.refrescar_trackers()
        self.assertEquals(len(ccs._trackers_campana_dict), 1)
        self.assertIn(campana1, ccs._trackers_campana_dict)
        self.assertTrue(ccs._trackers_campana_dict[campana1].activa)

        # Chequeamos q' agregue cuando hay trackers pre-existentes
        campana2 = self._crear_1_campana()

        ccs.refrescar_trackers()
        self.assertEquals(len(ccs._trackers_campana_dict), 2)
        self.assertIn(campana2, ccs._trackers_campana_dict)
        self.assertTrue(ccs._trackers_campana_dict[campana2].activa)

    def test__refrescar_trackers__desactiva_baneados(self):
        campana1 = self._crear_1_campana()
        campana2 = self._crear_1_campana()
        ccs = CampanaCallStatus()

        # -----

        ccs.refrescar_trackers()
        self.assertEquals(len(ccs._trackers_campana_dict), 2)
        self.assertIn(campana1, ccs._trackers_campana_dict)
        self.assertIn(campana2, ccs._trackers_campana_dict)

        # Baneamos y chequeamos
        ccs.banear_campana(campana2)
        ccs.refrescar_trackers()
        self.assertEquals(len(ccs._trackers_campana_dict), 2)
        self.assertIn(campana1, ccs._trackers_campana_dict)
        self.assertIn(campana2, ccs._trackers_campana_dict)

        # Check estado
        self.assertTrue(ccs._trackers_campana_dict[campana1].activa)
        self.assertFalse(ccs._trackers_campana_dict[campana2].activa)

    def test__refrescar_trackers__desactiva_campanas_no_en_curso(self):
        """Testea que los trackers creados anteriormente son desactivados
        si ya no deben ser tenidos en cuenta"""
        campana1 = self._crear_1_campana()
        campana2 = self._crear_1_campana()
        ccs = CampanaCallStatus()

        ccs.refrescar_trackers()
        self.assertEquals(len(ccs._trackers_campana_dict), 2)
        self.assertTrue(ccs._trackers_campana_dict[campana1].activa)
        self.assertTrue(ccs._trackers_campana_dict[campana2].activa)

        # -----

        # Finaliza campaña y refresca
        campana2.finalizar()
        ccs.refrescar_trackers()
        self.assertEquals(len(ccs._trackers_campana_dict), 2)
        self.assertTrue(ccs._trackers_campana_dict[campana1].activa)
        self.assertFalse(ccs._trackers_campana_dict[campana2].activa)

    def test__refrescar_trackers__genera_NoHayCampanaEnEjecucion(self):
        ccs = CampanaCallStatus()
        with self.assertRaises(NoHayCampanaEnEjecucion):
            ccs.refrescar_trackers()


class RefrescaTrackersActivosUT(LiveServerTestCase, FTSenderBaseTest,
    PollDaemonTestUtilsMixin):

    def test_no_consulta_bd(self):
        """Chequea q' no consulta la BD"""

        class CampanaCallStatusTmp(CampanaCallStatus):
            def _obtener_campanas_en_ejecucion(self):
                raise Exception("ERROR: no debio llamarse este metodo")

        ccs = CampanaCallStatusTmp()

        # -----

        with self.assertRaises(NoHayCampanaEnEjecucion):
            ccs.refrescar_trackers_activos()

    def test_genera_NoHayCampanaEnEjecucion(self):
        ccs = CampanaCallStatus()
        with self.assertRaises(NoHayCampanaEnEjecucion):
            ccs.refrescar_trackers()
        with self.assertRaises(NoHayCampanaEnEjecucion):
            ccs.refrescar_trackers_activos()

    def test_ignora_baneados_y_desbaneados(self):
        campana1 = self._crear_1_campana()
        campana2 = self._crear_1_campana()
        ccs = CampanaCallStatus()
        ccs.refrescar_trackers()

        # -----

        ccs.refrescar_trackers_activos()
        self.assertEquals(len(ccs.trackers_activos), 2)

        # baneamos...
        ccs.banear_campana(campana2)
        self.assertTrue(ccs._ban_manager.esta_baneada(campana2))

        # ... y chequeqamos
        ccs.refrescar_trackers_activos()
        self.assertEquals(len(ccs.trackers_activos), 1)
        self.assertEquals(ccs.trackers_activos[0].campana,
            campana1)

        # des-baneamos...
        ccs._ban_manager.des_banear(campana2)
        self.assertFalse(ccs._ban_manager.esta_baneada(campana2))

        # ... y chequeqamos
        ccs.refrescar_trackers_activos()
        self.assertEquals(len(ccs.trackers_activos), 1)
        self.assertEquals(ccs.trackers_activos[0].campana,
            campana1)


class LimitesDeLLamadasUT(LiveServerTestCase, FTSenderBaseTest,
    PollDaemonTestUtilsMixin):

    def test_todas_las_campanas_al_limite_devuelve_true(self):
        ccs = CampanaCallStatus()
        _ = self._crear_1_campana(tamano=2, cantidad_canales=1)
        _ = self._crear_1_campana(tamano=2, cantidad_canales=1)
        ccs.refrescar_trackers()

        self.assertFalse(ccs.todas_las_campanas_al_limite())
        ccs.trackers_activos[0].next()
        self.assertFalse(ccs.todas_las_campanas_al_limite())
        ccs.trackers_activos[1].next()
        self.assertTrue(ccs.todas_las_campanas_al_limite())

    def test_refrescar_con_todas_las_campanas_al_limite(self):
        """Chequeqa q' al refrescar, si todas las llamadas
        estan al limite, se continua al limite"""

        ccs = CampanaCallStatus()
        _ = self._crear_1_campana(tamano=2, cantidad_canales=1)
        _ = self._crear_1_campana(tamano=2, cantidad_canales=1)
        ccs.refrescar_trackers()
        ccs.trackers_activos[0].next()
        ccs.trackers_activos[1].next()
        self.assertTrue(ccs.todas_las_campanas_al_limite())

        # -----

        ccs.refrescar_trackers()
        self.assertTrue(ccs.todas_las_campanas_al_limite())

        ccs.refrescar_trackers_activos()
        self.assertTrue(ccs.todas_las_campanas_al_limite())

    @override_settings(FTS_LIMITE_GLOBAL_DE_CANALES=1)
    def test_limite_global_de_canales(self):
        ccs = CampanaCallStatus()
        _ = self._crear_1_campana(tamano=2, cantidad_canales=1)
        _ = self._crear_1_campana(tamano=2, cantidad_canales=1)
        ccs.refrescar_trackers()

        # -----

        self.assertFalse(ccs.limite_global_de_canales_alcanzado())
        ccs.trackers_activos[0].next()
        self.assertTrue(ccs.limite_global_de_canales_alcanzado())


class ObtencionDeTrackersUT(LiveServerTestCase, FTSenderBaseTest,
    PollDaemonTestUtilsMixin):

    def test_obtener_trackers_para_procesar_accede_bd(self):

        class LlamoMetodo(Exception):
            pass

        class CampanaCallStatusTmp(CampanaCallStatus):
            def _obtener_campanas_en_ejecucion(self):
                raise LlamoMetodo()

        ccs = CampanaCallStatusTmp()

        with self.assertRaises(LlamoMetodo):
            ccs.obtener_trackers_para_procesar()

    def test_obtener_trackers_para_procesar_devuelve_trackers(self):
        _ = self._crear_1_campana()
        _ = self._crear_1_campana()

        ccs = CampanaCallStatus()
        trackers = ccs.obtener_trackers_para_procesar()
        self.assertEqual(len(trackers), 2)

    def test_obtener_trackers_para_procesar_ignora_baneados(self):
        campana1 = self._crear_1_campana()
        campana2 = self._crear_1_campana()

        ccs = CampanaCallStatus()
        ccs.banear_campana(campana1)

        trackers = ccs.obtener_trackers_para_procesar()
        self.assertEqual(len(trackers), 1)
        self.assertEqual(trackers[0].campana, campana2)


class GetCountLlamadasUT(LiveServerTestCase, FTSenderBaseTest,
    PollDaemonTestUtilsMixin):

    def test_get_count_llamadas_devuelve_count_correcto(self):
        """Se testean varios escenarios:
        - workflow normal
        - con campanas baneadas
        - con campanas finalizadas
        """

        # Siempre refrescará los trackers
        class CampanaCallStatusSiempreNecesitaRefrescar(CampanaCallStatus):
            def _necesita_refrescar_trackers(self):
                return True

        campana = self._crear_1_campana(tamano=4, cantidad_canales=3)
        campana_baneada = self._crear_1_campana(
            tamano=4, cantidad_canales=2)
        campana_finalizada = self._crear_1_campana(
            tamano=4, cantidad_canales=2)

        ccs = CampanaCallStatusSiempreNecesitaRefrescar()

        # -----

        # Workflow normal
        trackers = ccs.obtener_trackers_para_procesar()
        self.assertEquals(len(trackers), 3)
        trackers[0].next()
        trackers[1].next()
        trackers[2].next()

        self.assertEquals(ccs.get_count_llamadas(), 3)

        # Baneamos y refresco
        ccs.banear_campana(campana_baneada)

        trackers = ccs.obtener_trackers_para_procesar()
        self.assertEquals(len(trackers), 2)
        trackers[0].next()
        trackers[1].next()

        self.assertEquals(ccs.get_count_llamadas(), 5)

        # Finalizamos y refrescamos
        campana_finalizada.finalizar()

        trackers = ccs.obtener_trackers_para_procesar()
        self.assertEquals(len(trackers), 1)
        trackers[0].next()

        self.assertEquals(ccs.get_count_llamadas(), 6)

        # a esta altura, `campana` esta al limite de canales

        trackers = ccs.obtener_trackers_para_procesar()
        self.assertEquals(len(trackers), 1)
        self.assertEquals(trackers[0].campana, campana)
        with self.assertRaises(LimiteDeCanalesAlcanzadoError):
            trackers[0].next()

        self.assertEquals(ccs.get_count_llamadas(), 6)


class UpdateCallStatusUT(LiveServerTestCase, FTSenderBaseTest,
    PollDaemonTestUtilsMixin):

    def test_actualiza_status_de_trackers_existentes(self):

        def _adapt(dprl):
            return (dprl.campana,
                    dprl.id_contacto,
                    dprl.telefono,
                    dprl.intentos,
                    )

        # Siempre refrescará los trackers
        class CampanaCallStatusSiempreNecesitaRefrescar(CampanaCallStatus):
            def _necesita_refrescar_trackers(self):
                return True

        ccs = CampanaCallStatusSiempreNecesitaRefrescar()

        campana1 = self._crear_1_campana(cantidad_canales=2)
        campana2 = self._crear_1_campana(cantidad_canales=2)

        # -----

        full_status = {
            campana1.id: [],
            campana2.id: [],
        }

        trackers = ccs.obtener_trackers_para_procesar()
        trackers_x_campana = dict([(t.campana, t) for t in trackers])

        # simulamos inicio de 4 llamadas
        campana, contacto_id, numero, _ = _adapt(trackers[0].next())
        full_status[campana.id].append([
            contacto_id, numero, campana.id
        ])

        campana, contacto_id, numero, _ = _adapt(trackers[0].next())
        full_status[campana.id].append([
            contacto_id, numero, campana.id
        ])

        campana, contacto_id, numero, _ = _adapt(trackers[1].next())
        full_status[campana.id].append([
            contacto_id, numero, campana.id
        ])

        campana, contacto_id, numero, _ = _adapt(trackers[1].next())
        full_status[campana.id].append([
            contacto_id, numero, campana.id
        ])

        self.assertEquals(ccs.get_count_llamadas(), 4)

        with self.assertRaises(LimiteDeCanalesAlcanzadoError):
            trackers[0].next()
        with self.assertRaises(LimiteDeCanalesAlcanzadoError):
            trackers[1].next()

        # actualizamos status
        ccs.update_call_status(full_status)

        self.assertEquals(ccs.get_count_llamadas(), 4)

        with self.assertRaises(LimiteDeCanalesAlcanzadoError):
            trackers[0].next()
        with self.assertRaises(LimiteDeCanalesAlcanzadoError):
            trackers[1].next()

        # Simulamos 1 canal liberado para campana 1
        full_status[campana1.id].pop()

        # actualizamos status
        ccs.update_call_status(full_status)

        self.assertEquals(ccs.get_count_llamadas(), 3)

        trackers_x_campana[campana1].next()

        self.assertEquals(ccs.get_count_llamadas(), 4)

        with self.assertRaises(LimiteDeCanalesAlcanzadoError):
            trackers_x_campana[campana1].next()

        with self.assertRaises(LimiteDeCanalesAlcanzadoError):
            trackers_x_campana[campana2].next()

        self.assertEquals(ccs.get_count_llamadas(), 4)

        # full_status -> dict
        #  * KEY -> campana_id
        #  * VALUE -> [
        #        [contacto_id, numero, campana_id],
        #        [contacto_id, numero, campana_id],
        #    ]
