# -*- coding: utf-8 -*-

"""Tests del componente scheduler / RRT"""

from __future__ import unicode_literals

from django.test.testcases import LiveServerTestCase
from django.test.utils import override_settings
from fts_daemon.models import EventoDeContacto
from fts_daemon.poll_daemon.call_status import AsteriskCallStatus
from fts_daemon.poll_daemon.main import main
from fts_daemon.poll_daemon.originate_throttler import OriginateThrottler
from fts_daemon.poll_daemon.scheduler import RoundRobinTracker, \
    CantidadMaximaDeIteracionesSuperada, Llamador
from fts_tests.tests.tests_asterisk_ami_http_mocks import \
    AsteriskAmiHttpClientBaseMock
from fts_tests.tests.tests_poll_daemon_campana_tracker import \
    PollDaemonTestUtilsMixin
from fts_tests.tests.utiles import EventoDeContactoAssertUtilesMixin
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
import mock


logger = _logging.getLogger(__name__)

CONT_PROG = EventoDeContacto.EVENTO_CONTACTO_PROGRAMADO
D_INI_INT = EventoDeContacto.EVENTO_DAEMON_INICIA_INTENTO
D_ORIG_SUC = EventoDeContacto.EVENTO_DAEMON_ORIGINATE_SUCCESSFUL


#==============================================================================
# Utilidades
#==============================================================================

class SleepDetectedError(Exception):
    """Indica q' se ha llamado a sleep()"""
    pass


class RRTSinSleep(RoundRobinTracker):
    """Base class for RoundRobinTracker without waits"""

    # Overriden
    def __init__(self, *args, **kwargs):
        RoundRobinTracker.__init__(self, *args, **kwargs)
        self.status_refrescado = False
        self.sleep_ejecutado = False
        self.max_iterations = 20
        self.raise_on_sleep = True

    # Overriden
    def real_sleep(self, segundos):
        self.sleep_ejecutado = True
        if self.raise_on_sleep:
            raise SleepDetectedError()

    def _finalizar_y_programar_depuracion(self, campana_id):
        pass


class AsteriskCallStatusDevuelveStatusVacioMock(AsteriskCallStatus):

    def _get_status_por_campana(self):
        return dict()


class RRTConRefrescoDeStatus(RRTSinSleep):
    """RoundRobinTracker, que al consultar status de llamadas,
    devuelve status como si no hubiera llamadas en curso
    """

    def __init__(self, *args, **kwargs):
        super(RRTConRefrescoDeStatus, self).__init__(*args, **kwargs)
        self._asterisk_call_status = AsteriskCallStatusDevuelveStatusVacioMock(
            self._campana_call_status)


class RRTQueGeneraErrorOnEventos(RRTSinSleep):
    """Implementacion de RRT que genera excepcion si se llama a alguno
    de los metodos onEventoXxx()"""

    def onCampanaNoEnEjecucion(self, campana):
        raise Exception("Se ha llamado onCampanaNoEnEjecucion")

    def onNoMasContactosEnCampana(self, campana):
        raise Exception("Se ha llamado onNoMasContactosEnCampana")

    def onLimiteDeCanalesAlcanzadoError(self, campana):
        raise Exception("Se ha llamado onLimiteDeCanalesAlcanzadoError")

    def onNoSeDevolvioContactoEnRoundActual(self):
        raise Exception("Se ha llamado onNoSeDevolvioContactoEnRoundActual")

    def onLimiteDeOriginatePorSegundosError(self, to_sleep):
        raise Exception("Se ha llamado onLimiteDeOriginatePorSegundosError")

    def onTodosLosContactosPendientesEstanEnCursoError(self, campana):
        raise Exception("Se ha llamado "
            "onTodosLosContactosPendientesEstanEnCursoError")

    def onTodasLasCampanasAlLimite(self):
        raise Exception("Se ha llamado "
            "onTodasLasCampanasAlLimite()")

    def _finalizar_y_programar_depuracion(self, campana_id):
        pass


#==============================================================================
# Tests
#==============================================================================

class RoundRobinTrackerTest(LiveServerTestCase, FTSenderBaseTest,
    PollDaemonTestUtilsMixin):

    def setUp(self):
        self.campana, self.campana1, self.campana3 = \
            self._crear_3_campanas()

    def test_generator_devuelve_contactos_de_campanas(self):
        # Preparacion y chequeos previos
        c_activas = list(Campana.objects.obtener_ejecucion())
        c_no_activas = [self.crear_campana_activa(10)]

        self.assertEquals(len(c_activas), 3)
        self.assertNotIn(c_no_activas[0], c_activas)

        rr_tracker = RRTQueGeneraErrorOnEventos()
        generator = rr_tracker.generator()

        # -----

        def _adapt(dprl):
            return (dprl.campana,
                    dprl.id_contacto,
                    dprl.telefono,
                    dprl.intentos,
                    )

        campana_a, id_contacto_a, numero_a, _ = _adapt(next(generator))
        campana_b, id_contacto_b, numero_b, _ = _adapt(next(generator))
        campana_c, id_contacto_c, numero_c, _ = _adapt(next(generator))
        campana_d, _, _, _ = _adapt(next(generator))

        metadata_a = campana_a.bd_contacto.get_metadata()
        metadata_b = campana_b.bd_contacto.get_metadata()
        metadata_c = campana_c.bd_contacto.get_metadata()

        self._assertContacto(id_contacto_a, numero_a, campana_a, metadata_a)
        self._assertContacto(id_contacto_b, numero_b, campana_b, metadata_b)
        self._assertContacto(id_contacto_c, numero_c, campana_c, metadata_c)

        self.assertIn(campana_a, c_activas)
        self.assertIn(campana_b, c_activas)
        self.assertIn(campana_c, c_activas)

        self.assertNotIn(campana_a, c_no_activas)
        self.assertNotIn(campana_b, c_no_activas)
        self.assertNotIn(campana_c, c_no_activas)

        self.assertNotEquals(campana_a, campana_b)
        self.assertNotEquals(campana_a, campana_c)

        self.assertTrue(campana_d == campana_a
            or campana_d == campana_b
            or campana_d == campana_c)

    def test_llamada_a_on_evento_no_produce_error(self):
        """Llama eventos para asegurarnos q' no producen errores"""

        rr_tracker = RRTSinSleep()

        # onNoSeDevolvioContactoEnRoundActual()
        rr_tracker.onNoSeDevolvioContactoEnRoundActual()

        # onLimiteDeOriginatePorSegundosError()
        rr_tracker.onLimiteDeOriginatePorSegundosError(1.0)

        # onLimiteDeCanalesAlcanzadoError()
        rr_tracker.onLimiteDeCanalesAlcanzadoError(self.campana)

        # onCampanaNoEnEjecucion()
        rr_tracker.onCampanaNoEnEjecucion(self.campana)

        # onLimiteGlobalDeCanalesAlcanzadoError()
        rr_tracker.onLimiteGlobalDeCanalesAlcanzadoError()

        # onNoMasContactosEnCampana()
        rr_tracker.onNoMasContactosEnCampana(self.campana)

        # onTodosLosContactosPendientesEstanEnCursoError()
        rr_tracker.onTodosLosContactosPendientesEstanEnCursoError(
            self.campana)

        # onTodasLasCampanasAlLimite()
        rr_tracker.onTodasLasCampanasAlLimite()

    def test_onCampanaNoEnEjecucion_banea(self):
        # Populamos RRT
        rr_tracker = RRTSinSleep()
        generator = rr_tracker.generator()
        next(generator)
        next(generator)
        next(generator)

        # -----

        self.assertFalse(rr_tracker._campana_call_status._ban_manager.\
            esta_baneada(self.campana))
        rr_tracker.onCampanaNoEnEjecucion(self.campana)
        # Banear 2 veces la misma campaña deberia funcionar
        rr_tracker.onCampanaNoEnEjecucion(self.campana)
        self.assertTrue(rr_tracker._campana_call_status._ban_manager.\
                esta_baneada(self.campana))

    def test_onNoMasContactosEnCampana_banea(self):
        # Populamos RRT
        rr_tracker = RRTSinSleep()
        generator = rr_tracker.generator()
        next(generator)
        next(generator)
        next(generator)

        # -----

        self.assertFalse(rr_tracker._campana_call_status._ban_manager.\
            esta_baneada(self.campana))
        rr_tracker.onNoMasContactosEnCampana(self.campana)
        self.assertTrue(rr_tracker._campana_call_status._ban_manager.\
            esta_baneada(self.campana))

    def test_onTodosLosContactosPendientesEstanEnCursoError_banea(self):

        self.campana.cantidad_canales = 3
        self.campana.save()
        self.campana1.cantidad_canales = 3
        self.campana1.save()
        self.campana3.cantidad_canales = 3
        self.campana3.save()

        def _adapt(dprl):
            return (dprl.campana,
                    dprl.id_contacto,
                    dprl.telefono,
                    dprl.intentos,
                    )

        # Populamos RRT
        rr_tracker = RRTConRefrescoDeStatus()
        generator = rr_tracker.generator()

        c1, _, _, _ = _adapt(next(generator))
        c2, _, _, _ = _adapt(next(generator))
        c3, _, _, _ = _adapt(next(generator))

        # Verificamos q' devuelve de las 3 campanas
        self.assertEqual(len(set([c1, c2, c3])), 3)

        # -----

        self.assertFalse(rr_tracker._campana_call_status._ban_manager.\
            esta_baneada(self.campana))
        rr_tracker.onTodosLosContactosPendientesEstanEnCursoError(self.campana)
        self.assertTrue(rr_tracker._campana_call_status._ban_manager.\
            esta_baneada(self.campana))

        c1, _, _, _ = _adapt(next(generator))
        c2, _, _, _ = _adapt(next(generator))
        c3, _, _, _ = _adapt(next(generator))
        c4, _, _, _ = _adapt(next(generator))

        # Verificamos q' baneo funciona
        self.assertEqual(len(set([c1, c2, c3, c4])), 2)
        self.assertNotIn(self.campana, [c1, c2, c3, c4])

    def test_detecta_todas_las_campanas_al_limite(self):

        # Mock q' NO refresca status
        asterisk_call_status = mock.Mock(spec=AsteriskCallStatus)
        asterisk_call_status.refrescar_channel_status = \
            mock.MagicMock(return_value=None)

        # Mock de RRT
        rr_tracker = RRTSinSleep()
        rr_tracker.raise_on_sleep = False
        rr_tracker.max_iterations = 5
        rr_tracker._asterisk_call_status = asterisk_call_status
        rr_tracker.onTodasLasCampanasAlLimite = \
            mock.MagicMock(return_value=None)

        generator = rr_tracker.generator()

        # -----

        next(generator)
        next(generator)
        next(generator)

        next(generator)
        next(generator)
        next(generator)

        self.assertFalse(rr_tracker.onTodasLasCampanasAlLimite.called)

        with self.assertRaises(CantidadMaximaDeIteracionesSuperada):
            next(generator)

        self.assertTrue(rr_tracker.onTodasLasCampanasAlLimite.called)

    @override_settings(FTS_LIMITE_GLOBAL_DE_CANALES=2)
    def test_detecta_limite_global_de_canales_alcanzados(self):

        # Mock q' NO refresca status
        asterisk_call_status = mock.Mock(spec=AsteriskCallStatus)
        asterisk_call_status.refrescar_channel_status = \
            mock.MagicMock(return_value=None)

        # Mock de RRT
        rr_tracker = RRTSinSleep()
        rr_tracker.raise_on_sleep = False
        rr_tracker.max_iterations = 5
        rr_tracker._asterisk_call_status = asterisk_call_status
        rr_tracker.onLimiteGlobalDeCanalesAlcanzadoError = \
            mock.MagicMock(return_value=None)

        generator = rr_tracker.generator()

        # -----

        next(generator)
        next(generator)

        self.assertFalse(
            rr_tracker.onLimiteGlobalDeCanalesAlcanzadoError.called)

        with self.assertRaises(CantidadMaximaDeIteracionesSuperada):
            next(generator)

        self.assertTrue(
            rr_tracker.onLimiteGlobalDeCanalesAlcanzadoError.called)

#
# Lo testeado en el siguiente test, ahora esta en otro componente
#  asi q' no tiene sentido re-testearlo aca
#
# class RefrescarChannelStatusLlamadasEnCursoTest(LiveServerTestCase,
#    FTSenderBaseTest, PollDaemonTestUtilsMixin,
#    EventoDeContactoAssertUtilesMixin):
#    """Chequea refrescar_channel_status() cuando no devuelve ninguna campana,
#    una campana o 2 campanas (este ultimo caso implica q' la campana esta
#    al limite).
#    """
#
#    def _get_logger(self):
#        return logger
#
#    def setUp(self):
#        self.campana = self._crear_1_campana()
#
#    def test_refrescar_channel_status_sin_llamadas(self):
#        """Chequea cuando no hay llamadas en curso"""
#
#        rr_tracker = RRTSinSleep()
#        generator = rr_tracker.generator()
#
#        def _tc():
#            """Devuelve tracker de campana"""
#            return rr_tracker.trackers_campana[self.campana]
#
#        # -----
#
#        self.assertEquals(rr_tracker.status_refrescado, False)
#
#        next(generator)
#        self.assertEquals(rr_tracker.status_refrescado, False)
#        self.assertEquals(_tc().llamadas_en_curso_aprox, 1)
#
#        next(generator)
#        self.assertEquals(rr_tracker.status_refrescado, False)
#        self.assertEquals(_tc().llamadas_en_curso_aprox, 2)
#
#        custom_status_values = [
#            # [campana_id, contacto_id, telefono]
#            # [self.campana.id, 1000, "01140008000"],
#        ]
#
#        with override_settings(
#            HTTP_AMI_URL=self._code('status-llamada-en-local-channel-CUSTOM'),
#            CUSTOM_STATUS_VALUES=custom_status_values):
#            next(generator)
#
#        self.assertEquals(_tc().llamadas_en_curso_aprox, 1)
#        self.assertEquals(rr_tracker.status_refrescado, True)
#
#    def __test_status_con_llamadas(self, custom_status_values, check):
#
#        rr_tracker = RRTSinSleep()
#        generator = rr_tracker.generator()
#
#        def _tc():
#            """Devuelve tracker de campana"""
#            return rr_tracker.trackers_campana[self.campana]
#
#        # -----
#
#        self.assertEquals(rr_tracker.status_refrescado, False)
#
#        next(generator)
#        self.assertEquals(rr_tracker.status_refrescado, False)
#        self.assertEquals(_tc().llamadas_en_curso_aprox, 1)
#
#        next(generator)
#        self.assertEquals(rr_tracker.status_refrescado, False)
#        self.assertEquals(_tc().llamadas_en_curso_aprox, 2)
#
#        with override_settings(
#            HTTP_AMI_URL=self._code('status-llamada-en-local-channel-CUSTOM'),
#            CUSTOM_STATUS_VALUES=custom_status_values):
#
#            check(generator, rr_tracker, _tc())
#
#    def test_refrescar_channel_status_solo_con_extra(self):
#        """Chequea cuando campana no posee status, pero si hay info
#        de otras campanas
#        """
#
#        custom_status_values = [
#            # [campana_id, contacto_id, telefono]
#            [self.campana.id + 7, 7000, "01140008070", 1],
#            [self.campana.id + 7, 7001, "01140008071", 1],
#            [self.campana.id + 7, 7002, "01140008072", 1],
#        ]
#
#        def check(generator, rr_tracker, tracker):
#            next(generator)
#            self.assertEquals(tracker.llamadas_en_curso_aprox, 1)
#            self.assertEquals(rr_tracker.status_refrescado, True)
#
#        self.__test_status_con_llamadas(custom_status_values, check)
#
#    def test_refrescar_channel_status_con_1_llamada(self):
#        """Chequea cuando campana no ha llegado al limite"""
#
#        custom_status_values = [
#            # [campana_id, contacto_id, telefono]
#            [self.campana.id, 1000, "01140008000", 1],
#        ]
#
#        def check(generator, rr_tracker, tracker):
#            next(generator)
#            self.assertEquals(tracker.llamadas_en_curso_aprox, 2)
#            self.assertEquals(rr_tracker.status_refrescado, True)
#
#        self.__test_status_con_llamadas(custom_status_values, check)
#
#    def test_refrescar_channel_status_con_1_llamada_mas_extra(self):
#        """Chequea cuando campana no ha llegado al limite"""
#
#        custom_status_values = [
#            # [campana_id, contacto_id, telefono]
#            [self.campana.id, 1000, "01140008000", 1],
#            [self.campana.id + 7, 7000, "01140008070", 1],
#            [self.campana.id + 7, 7001, "01140008071", 1],
#            [self.campana.id + 7, 7002, "01140008072", 1],
#        ]
#
#        def check(generator, rr_tracker, tracker):
#            next(generator)
#            self.assertEquals(tracker.llamadas_en_curso_aprox, 2)
#            self.assertEquals(rr_tracker.status_refrescado, True)
#
#        self.__test_status_con_llamadas(custom_status_values, check)
#
#    def test_refrescar_channel_status_con_2_llamadas(self):
#        """Chequea cuando todas las campanas estan al limite"""
#
#        # ~~~~~ Testeamos como si 2 llamadas estuvieran en curso
#        custom_status_values = [
#            [self.campana.id, 1000, "01140008000", 1],
#            [self.campana.id, 1001, "01140008001", 1],
#        ]
#
#        def check(generator, rr_tracker, tracker):
#            with self.assertRaises(SleepDetectedError):
#                next(generator)
#
#        self.__test_status_con_llamadas(custom_status_values, check)
#
#    def test_refrescar_channel_status_con_2_llamadas_mas_extra(self):
#        """Chequea cuando todas las campanas estan al limite"""
#
#        # ~~~~~ Testeamos como si 2 llamadas estuvieran en curso
#        custom_status_values = [
#            [self.campana.id, 1000, "01140008000", 1],
#            [self.campana.id, 1001, "01140008001", 1],
#            [self.campana.id + 7, 7000, "01140008070", 1],
#            [self.campana.id + 7, 7001, "01140008071", 1],
#            [self.campana.id + 7, 7002, "01140008072", 1],
#        ]
#
#        def check(generator, rr_tracker, tracker):
#            with self.assertRaises(SleepDetectedError):
#                next(generator)
#
#        self.__test_status_con_llamadas(custom_status_values, check)
#
#    def test_refrescar_channel_status_con_3_llamadas(self):
#        """Chequea cuando hay mas llamadas en curso que las
#        especificadas en el limite de la campana
#        """
#
#        # ~~~~~ Testeamos como si 3 llamadas estuvieran en curso
#        custom_status_values = [
#            # [campana_id, contacto_id, telefono]
#            [self.campana.id, 1000, "01140008000", 1],
#            [self.campana.id, 1001, "01140008001", 1],
#            [self.campana.id, 1002, "01140008002", 1],
#        ]
#
#        def check(generator, rr_tracker, tracker):
#            with self.assertRaises(SleepDetectedError):
#                next(generator)
#
#        self.__test_status_con_llamadas(custom_status_values, check)
#
#    def test_refrescar_channel_status_con_3_llamadas_mas_extras(self):
#        """Chequea cuando hay mas llamadas en curso que las
#        especificadas en el limite de la campana
#        """
#
#        # ~~~~~ Testeamos como si 3 llamadas estuvieran en curso
#        custom_status_values = [
#            # [campana_id, contacto_id, telefono]
#            [self.campana.id, 1000, "01140008000", 1],
#            [self.campana.id, 1001, "01140008001", 1],
#            [self.campana.id, 1002, "01140008002", 1],
#            [self.campana.id + 7, 7000, "01140008070", 1],
#            [self.campana.id + 7, 7001, "01140008071", 1],
#            [self.campana.id + 7, 7002, "01140008072", 1],
#        ]
#
#        def check(generator, rr_tracker, tracker):
#            with self.assertRaises(SleepDetectedError):
#                next(generator)
#
#        self.__test_status_con_llamadas(custom_status_values, check)


#class RoundRobinTrackerTestOnEventos(FTSenderBaseTest,
#    PollDaemonTestUtilsMixin):
#
#    def setUp(self):
#        pass
#
##    def test_llama_onNoSeDevolvioContactoEnRoundActual(self):
##        """Chequea que se llame onNoSeDevolvioContactoEnRoundActual()"""
##
##        class DetectoNoSeDevolvioContactoEnRoundActual(Exception):
##            pass
##
##        class Tmp2RoundRobinTracker(RRTSinSleep):
##
##            def onNoSeDevolvioContactoEnRoundActual(self):
##                raise DetectoNoSeDevolvioContactoEnRoundActual()
##
##        rr_tracker = Tmp2RoundRobinTracker()
##        generator = rr_tracker.generator()
##
##        with self.assertRaises(DetectoNoSeDevolvioContactoEnRoundActual):
##            next(generator)
#
#    def test_llama_onNoHayCampanaEnEjecucion(self):
#        """Chequea que se llame onNoHayCampanaEnEjecucion()"""
#
#        class DetectoOnNoHayCampanaEnEjecucion(Exception):
#            pass
#
#        class Tmp2RoundRobinTracker(RRTSinSleep):
#
#            def onNoHayCampanaEnEjecucion(self):
#                raise DetectoOnNoHayCampanaEnEjecucion()
#
#        rr_tracker = Tmp2RoundRobinTracker()
#        generator = rr_tracker.generator()
#
#        # -----
#
#        with self.assertRaises(DetectoOnNoHayCampanaEnEjecucion):
#            next(generator)
#
#    def test_llama_onCampanaNoEnEjecucion(self):
#        """Chequea que se llame onCampanaNoEnEjecucion()"""
#
#        class DetectoOnCampanaNoEnEjecucion(Exception):
#            pass
#
#        class Tmp2RoundRobinTracker(RRTSinSleep):
#
#            def onCampanaNoEnEjecucion(self, campana):
#                super(Tmp2RoundRobinTracker, self).onCampanaNoEnEjecucion(
#                    campana)
#                raise DetectoOnCampanaNoEnEjecucion()
#
#        self.campana = self.crear_campana_activa(cant_contactos=5,
#            cantidad_canales=2)
#        self.crea_todas_las_actuaciones(self.campana)
#
#        rr_tracker = Tmp2RoundRobinTracker()
#        generator = rr_tracker.generator()
#
#        # -----
#
#        next(generator)
#
#        self.assertFalse(rr_tracker._campana_call_status._ban_manager.\
#            campanas_baneadas)
#
#        self.campana.estado = Campana.ESTADO_PAUSADA
#        self.campana.save()
#
#        with self.assertRaises(DetectoOnCampanaNoEnEjecucion):
#            next(generator)
#
#        self.assertTrue(self.campana in
#            rr_tracker._campana_call_status._ban_manager.campanas_baneadas)
#
#    def test_llama_onNoMasContactosEnCampana(self):
#        """Chequea que se llame onNoMasContactosEnCampana()"""
#
#        class DetectoOnNoMasContactosEnCampana(Exception):
#            pass
#
#        class Tmp2RoundRobinTracker(RRTSinSleep):
#
#            def onNoMasContactosEnCampana(self, campana):
#                super(Tmp2RoundRobinTracker, self).onNoMasContactosEnCampana(
#                    campana)
#                raise DetectoOnNoMasContactosEnCampana()
#
#        self.campana = self.crear_campana_activa(cant_contactos=2,
#            cantidad_canales=1)
#        self.crea_todas_las_actuaciones(self.campana)
#
#        rr_tracker = Tmp2RoundRobinTracker()
#        generator = rr_tracker.generator()
#
#        # -----
#
#        campana, contacto_id, _, _ = next(generator)
#        self.registra_evento_de_intento(campana.id, contacto_id, 1)
#        self.registra_evento_de_finalizacion(campana.id, contacto_id, 1)
#        rr_tracker.trackers_campana[campana].contactos_en_curso = []
#
#        campana, contacto_id, _, _ = next(generator)
#        self.registra_evento_de_intento(campana.id, contacto_id, 1)
#        self.registra_evento_de_finalizacion(campana.id, contacto_id, 1)
#        rr_tracker.trackers_campana[campana].contactos_en_curso = []
#
#        with self.assertRaises(DetectoOnNoMasContactosEnCampana):
#            next(generator)
#
#        self.assertTrue(self.campana in
#            rr_tracker._campana_call_status._ban_manager.campanas_baneadas)
#
#    @override_settings(FTS_DAEMON_ORIGINATES_PER_SECOND=10.0)
#    def test_llama_onLimiteDeOriginatePorSegundosError_10xseg(self):
#        """Chequea que se llame onLimiteDeOriginatePorSegundosError()
#        cuando el limite se a alcanzado
#        """
#
#        self.campana = self.crear_campana_activa(cant_contactos=5,
#            cantidad_canales=4)
#        self.crea_todas_las_actuaciones(self.campana)
#
#        class DetectoLimite(Exception):
#            pass
#
#        class Tmp2RoundRobinTracker(RRTSinSleep):
#
#            def onLimiteDeOriginatePorSegundosError(self, ignore):
#                raise DetectoLimite()
#
#        rr_tracker = Tmp2RoundRobinTracker()
#        rr_tracker.raise_on_sleep = False
#
#        generator = rr_tracker.generator()
#
#        # -----
#
#        next(generator)
#        rr_tracker.originate_throttler.set_originate(True)
#
#        with self.assertRaises(DetectoLimite):
#            next(generator)
#
#    @override_settings(FTS_DAEMON_ORIGINATES_PER_SECOND=10.0)
#    def test_no_llama_onLimiteDeOriginatePorSegundosError_10xseg(self):
#        """Chequea que NO se llame onLimiteDeOriginatePorSegundosError()
#        ya que el limite no se ha alcanzado
#        """
#
#        self.campana = self.crear_campana_activa(cant_contactos=5,
#            cantidad_canales=4)
#        self.crea_todas_las_actuaciones(self.campana)
#
#        class DetectoLimite(Exception):
#            pass
#
#        class Tmp2RoundRobinTracker(RRTSinSleep):
#
#            def onLimiteDeOriginatePorSegundosError(self, ignore):
#                raise DetectoLimite()
#
#        rr_tracker = Tmp2RoundRobinTracker()
#        rr_tracker.raise_on_sleep = False
#
#        generator = rr_tracker.generator()
#
#        # -----
#
#        next(generator)
#        rr_tracker.originate_throttler.set_originate(True)
#
#        # Ahora esperamos 0.1 seg. para asegurarnos que no superemos el limite
#        time.sleep(0.11)
#        next(generator)
#
#    def test_llama_onTodosLosContactosPendientesEstanEnCursoError(self):
#
#        self.campana = self.crear_campana_activa(cant_contactos=4,
#            cantidad_canales=3)
#        self.crea_todas_las_actuaciones(self.campana)
#
#        class OnEventoLlamaod(Exception):
#            pass
#
#        class TmpRRT(RRTSinSleep):
#
#            def onTodosLosContactosPendientesEstanEnCursoError(self, ignore):
#                raise OnEventoLlamaod()
#
#        rr_tracker = TmpRRT()
#        generator = rr_tracker.generator()
#
#        # -----
#
#        # Finalizo 2
#        campana, contacto_id, _, _ = next(generator)
#        self.registra_evento_de_finalizacion(campana.id, contacto_id, 1)
#
#        campana, contacto_id, _, _ = next(generator)
#        self.registra_evento_de_finalizacion(campana.id, contacto_id, 1)
#
#        # Reseteo tracker
#        rr_tracker.set_contactos_en_curso_de_campana(campana, [])
#
#        # A esta altura, quedan 2 pendientes, y ninguno en curso
#        campana, contacto_id, _, _ = next(generator)
#        campana, contacto_id, _, _ = next(generator)
#
#        # A esta altura, quedan los mismos 2 pendientes, esos 2 en curso
#        # y 1 canal libre.
#
#        with self.assertRaises(OnEventoLlamaod):
#            next(generator)
#
#
##    def test_llama_onLimiteDeCanalesAlcanzadoError(self):
##        """Chequea que se llame onLimiteDeCanalesAlcanzadoError()"""
##
##        class DetectoOnLimiteDeCanalesAlcanzadoError(Exception):
##            pass
##
##        class Tmp2RoundRobinTracker(RRTSinSleep):
##
##            def onLimiteDeCanalesAlcanzadoError(self, campana):
##                super(Tmp2RoundRobinTracker, self).\
##                    onLimiteDeCanalesAlcanzadoError(campana)
##                raise DetectoOnLimiteDeCanalesAlcanzadoError()
##
##        self.campana = self.crear_campana_activa(cant_contactos=1)
##        self.assertEquals(self.campana.cantidad_canales, 2)
##        self.crea_todas_las_actuaciones(self.campana)
##
##        rr_tracker = Tmp2RoundRobinTracker()
##        generator = rr_tracker.generator()
##
##        next(generator)
##
##        tracker_campana = rr_tracker.trackers_campana[self.campana]
##        self.assertEquals(tracker_campana.llamadas_en_curso_aprox, 1)
##
##        next(generator)
##
##        self.assertEquals(tracker_campana.llamadas_en_curso_aprox, 2)
##
##        with self.assertRaises(DetectoOnLimiteDeCanalesAlcanzadoError):
##            next(generator)


#==============================================================================
# OriginateThrottler
#==============================================================================

class TestOriginateThrottlerTimeToSleep(FTSenderBaseTest):

    @override_settings(FTS_DAEMON_ORIGINATES_PER_SECOND=1.0)
    def test_sleep_inicial_es_cero(self):
        limit = OriginateThrottler()
        self.assertEquals(limit.time_to_sleep(), 0.0)

    @override_settings(FTS_DAEMON_ORIGINATES_PER_SECOND=0.0)
    def test_espera_cero_si_fue_configurado_sin_limite(self):
        limit = OriginateThrottler()
        self.assertEquals(limit.time_to_sleep(), 0.0)
        limit.set_originate(True)
        self.assertEquals(limit.time_to_sleep(), 0.0)

    @override_settings(FTS_DAEMON_ORIGINATES_PER_SECOND=10.0)
    def test_genera_sleep_correcto_10xseg(self):
        limit = OriginateThrottler()
        self.assertEquals(limit.time_to_sleep(), 0.0)
        limit.set_originate(True)
        to_sleep = limit.time_to_sleep()
        self.assertGreater(to_sleep, 0.0)
        self.assertLess(to_sleep, 1.0 / 10.0)

    @override_settings(FTS_DAEMON_ORIGINATES_PER_SECOND=1.0)
    def test_genera_sleep_correcto_1xseg(self):
        limit = OriginateThrottler()
        self.assertEquals(limit.time_to_sleep(), 0.0)
        limit.set_originate(True)
        to_sleep = limit.time_to_sleep()
        self.assertGreater(to_sleep, 0.8)  # 0.2 seg. de margen
        self.assertLess(to_sleep, 1.0)

    @override_settings(FTS_DAEMON_ORIGINATES_PER_SECOND=0.2)
    def test_genera_sleep_correcto_1_cada_5_seg(self):
        limit = OriginateThrottler()
        self.assertEquals(limit.time_to_sleep(), 0.0)
        limit.set_originate(True)
        to_sleep = limit.time_to_sleep()
        self.assertGreater(to_sleep, 4.8)  # 0.2 seg. de margen
        self.assertLess(to_sleep, 5.0)

    @override_settings(FTS_DAEMON_ORIGINATES_PER_SECOND=1.0)
    def test_devuelve_sleep_cero_si_originate_fallo(self):
        limit = OriginateThrottler()
        self.assertEquals(limit.time_to_sleep(), 0.0)
        limit.set_originate(False)
        self.assertEquals(limit.time_to_sleep(), 0.0)


#==============================================================================
# main()
#==============================================================================

class TestMain(FTSenderBaseTest, PollDaemonTestUtilsMixin,
    EventoDeContactoAssertUtilesMixin):

    def _get_logger(self):
        return logger

    def setUp(self):
        self.campana = self._crear_1_campana()
        self.cant_contactos = self.campana.bd_contacto.get_cantidad_contactos()

    def test_main_procesa_contactos(self):
        mock = AsteriskAmiHttpClientBaseMock.NAME
        self._assertCountEventos(self.campana, CONT_PROG)

        with override_settings(FTS_ASTERISK_HTTP_CLIENT=mock):
            main(max_loop=1, initial_wait=0.001)

        self._assertCountEventos(self.campana, CONT_PROG, D_INI_INT,
            D_ORIG_SUC, checks={CONT_PROG: self.cant_contactos,
                D_INI_INT: 1, D_ORIG_SUC: 1})

    @override_settings(FTS_DAEMON_ORIGINATES_PER_SECOND=1.0)
    def test_detecta_limite_originate_por_segundos(self):

        # Mock de RRT
        rr_tracker = RRTConRefrescoDeStatus()
        rr_tracker.raise_on_sleep = False
        rr_tracker.max_iterations = 5

        rr_tracker.onLimiteDeOriginatePorSegundosError = mock.Mock(
            spec=RRTConRefrescoDeStatus.onLimiteDeOriginatePorSegundosError)

        # -----

        llamador = Llamador()
        llamador.rr_tracker = rr_tracker
        llamador.procesar_contacto = mock.MagicMock(return_value=True)

        llamador.run(2)
        self.assertTrue(rr_tracker.onLimiteDeOriginatePorSegundosError.called)
