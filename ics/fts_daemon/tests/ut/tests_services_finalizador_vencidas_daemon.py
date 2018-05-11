# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.finalizador_de_campana.\
    finalizador_vencidas_daemon"""

from __future__ import unicode_literals

from fts_daemon.services.finalizador_vencidas_daemon import \
    FinalizadorDeCampanasVencidasDaemon
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock, patch
from django.test.utils import override_settings


logger = _logging.getLogger(__name__)


class FinalizadorDeCampanasVencidasDaemonTests(FTSenderBaseTest):
    """Unit tests de FinalizadorDeCampanasVencidasDaemon"""

    def test_finaliza_vencida(self):
        """Testea que finaliza campanas vencidas"""
        campana = Campana(id=1)
        campana.estado = Campana.ESTADO_ACTIVA
        finalizador = FinalizadorDeCampanasVencidasDaemon(max_loop=1,
                                                          initial_wait=0)
        finalizador._obtener_vencidas = Mock(return_value=[campana])
        finalizador._finalizar_y_programar_depuracion = Mock(return_value=None)
        finalizador._programar_depuracion = Mock(return_value=None)

        finalizador.run()

        finalizador._obtener_vencidas.assert_called_once_with()
        finalizador._finalizar_y_programar_depuracion.assert_called_once_with(
            campana)
        self.assertEqual(finalizador._programar_depuracion.call_count, 0)

    def test_progrograma_depuracion_de_finalizadas(self):
        """Testea que programa depuracion de finalizadas"""
        campana = Campana(id=1)
        campana.estado = Campana.ESTADO_FINALIZADA
        finalizador = FinalizadorDeCampanasVencidasDaemon(max_loop=1,
                                                          initial_wait=0)
        finalizador._obtener_vencidas = Mock(return_value=[])
        finalizador._obtener_finalizadas_por_depurar = Mock(
            return_value=[campana])

        finalizador._finalizar_y_programar_depuracion = Mock(return_value=None)
        finalizador._programar_depuracion = Mock(return_value=None)

        finalizador.run()

        finalizador._obtener_vencidas.assert_called_once_with()
        finalizador._programar_depuracion.assert_called_once_with(
            campana)
        self.assertEqual(
            finalizador._finalizar_y_programar_depuracion.call_count, 0)

    def test_no_hace_nada_sin_campanas(self):
        """Testea que no hace nada si no hay vencidas.
        Tambien testea q' no se actualice el status si no hay campanas
        por finalizar
        """
        finalizador = FinalizadorDeCampanasVencidasDaemon(max_loop=5,
                                                          initial_wait=0)
        finalizador._obtener_vencidas = Mock(return_value=[])
        finalizador._finalizar_async = Mock(return_value=None)
        finalizador._sleep = Mock(return_value=None)

        finalizador.run()

        self.assertEqual(finalizador._obtener_vencidas.call_count, 5)
        self.assertEqual(finalizador._finalizar_async.call_count, 0)

        # Ya que no habia camppañas, no se debio actualizar el status

    @patch("fts_daemon.tasks.esperar_y_depurar_campana")
    def test_metodo_finalizar_y_programar_depuracion(self, func_mock):
        """Testea el metodo finalizar_y_programar_depuracion()"""
        func_mock.delay = Mock()
        campana = Campana(id=1)
        campana.estado = Campana.ESTADO_ACTIVA
        campana.finalizar = Mock()

        finalizador = FinalizadorDeCampanasVencidasDaemon(initial_wait=0)

        # -----

        finalizador._finalizar_y_programar_depuracion(campana)

        func_mock.delay.assert_called_once_with(campana.id)
        campana.finalizar.assert_called_once_with()

    @patch("fts_daemon.tasks.esperar_y_depurar_campana")
    def test_metodo_programar_depuracion(self, func_mock):
        """Testea el metodo _programar_depuracion()"""
        func_mock.delay = Mock()
        campana = Campana(id=1)
        campana.estado = Campana.ESTADO_ACTIVA

        finalizador = FinalizadorDeCampanasVencidasDaemon(initial_wait=0)

        # -----

        finalizador._programar_depuracion(campana)

        func_mock.delay.assert_called_once_with(campana.id)

    def test_run_realiza_busqueda(self):
        """Testea que al ejecutar run(), se ejecuta la busqueda"""

        finalizador = FinalizadorDeCampanasVencidasDaemon(max_loop=1,
                                                          initial_wait=0)
        finalizador._obtener_vencidas = Mock(return_value=[])

        # -----

        finalizador.run()

        self.assertEqual(finalizador._obtener_vencidas.call_count, 1)


class TestsConstructor(FTSenderBaseTest):
    """Unit tests de constructor"""

    @override_settings(FTS_FDCD_INITIAL_WAIT=0.0001)
    def test_initial_wait_desde_settings(self):
        finalizador = FinalizadorDeCampanasVencidasDaemon()
        self.assertEquals(finalizador.initial_wait, 0.0001)

    @override_settings(FTS_FDCD_INITIAL_WAIT=0.0001)
    def test_initial_wait_sobreescrito_en_constructor(self):
        finalizador = FinalizadorDeCampanasVencidasDaemon(initial_wait=0.001)
        self.assertEquals(finalizador.initial_wait, 0.001)


class TestsMetodosVarios(FTSenderBaseTest):
    """Unit tests de los metodos utilitarios de
    FinalizadorDeCampanasVencidasDaemon
    """

    @patch("time.sleep")
    @override_settings(FTS_FDCD_INITIAL_WAIT=0,
                       FTS_FDCD_LOOP_SLEEP=34)
    def test_sleep(self, sleep_mock):
        finalizador = FinalizadorDeCampanasVencidasDaemon()
        finalizador._sleep()
        sleep_mock.assert_called_once_with(34)
