# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.finalizador_vencidas_daemon"""

from __future__ import unicode_literals

from fts_daemon.finalizador_vencidas_daemon.main import FinalizadorDeCampanas
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock


logger = _logging.getLogger(__name__)


class FinalizadorDeCampanasTests(FTSenderBaseTest):
    """Unit tests de FinalizadorDeCampanas"""

    def test_finaliza_vencida(self):
        """Testea que finaliza campanas vencidas"""
        campana = Campana(id=1)
        finalizador = FinalizadorDeCampanas(max_loop=1, initial_wait=0)
        finalizador._obtener_vencidas = Mock(return_value=[campana])
        finalizador._refrescar_status = Mock(return_value=True)
        finalizador._get_count_llamadas = Mock(return_value=0)
        finalizador._finalizar = Mock(return_value=None)

        finalizador.run()

        finalizador._obtener_vencidas.assert_called_once_with()
        finalizador._refrescar_status.assert_called_once_with()
        finalizador._get_count_llamadas.assert_called_once_with(campana)
        finalizador._finalizar.assert_called_once_with(campana)

    def test_no_finaliza_si_hay_llamada_en_curso(self):
        """Testea que NO finaliza campana si posee llamadas en curso"""
        campana = Campana(id=1)
        finalizador = FinalizadorDeCampanas(max_loop=1, initial_wait=0)
        finalizador._obtener_vencidas = Mock(return_value=[campana])
        finalizador._refrescar_status = Mock(return_value=True)
        finalizador._get_count_llamadas = Mock(return_value=1)
        finalizador._finalizar = Mock(return_value=None)

        finalizador.run()

        finalizador._obtener_vencidas.assert_called_once_with()
        finalizador._refrescar_status.assert_called_once_with()
        finalizador._get_count_llamadas.assert_called_once_with(campana)
        self.assertEqual(finalizador._finalizar.call_count, 0)

    def test_no_hace_nada_sin_campanas(self):
        """Testea que no hace nada si no hay vencidas.
        Tambien testea q' no se actualice el status si no hay campanas
        por finalizar
        """
        finalizador = FinalizadorDeCampanas(max_loop=5, initial_wait=0)
        finalizador._obtener_vencidas = Mock(return_value=[])
        finalizador._refrescar_status = Mock(return_value=True)
        finalizador._get_count_llamadas = Mock(return_value=0)
        finalizador._finalizar = Mock(return_value=None)
        finalizador._sleep = Mock(return_value=None)

        finalizador.run()

        self.assertEqual(finalizador._obtener_vencidas.call_count, 5)
        self.assertEqual(finalizador._get_count_llamadas.call_count, 0)
        self.assertEqual(finalizador._finalizar.call_count, 0)

        # Ya que no habia camppañas, no se debio actualizar el status
        self.assertEqual(finalizador._refrescar_status.call_count, 0)

    def test_no_finaliza_si_no_puede_chequear_status(self):
        """Testea que no se finalice la campana si no se pudo actualizar
        el status de llamadas en curso"""
        campana = Campana(id=1)
        finalizador = FinalizadorDeCampanas(max_loop=1, initial_wait=0)
        finalizador._obtener_vencidas = Mock(return_value=[campana])
        finalizador._refrescar_status = Mock(return_value=False)
        finalizador._get_count_llamadas = Mock(return_value=0)
        finalizador._finalizar = Mock(return_value=None)

        finalizador.run()

        finalizador._obtener_vencidas.assert_called_once_with()
        finalizador._refrescar_status.assert_called_once_with()
        self.assertEqual(finalizador._get_count_llamadas.call_count, 0)
        self.assertEqual(finalizador._finalizar.call_count, 0)
