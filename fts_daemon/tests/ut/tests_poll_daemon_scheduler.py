# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.poll_daemon.scheduler"""

from __future__ import unicode_literals

from fts_daemon.poll_daemon.scheduler import (
    RoundRobinTracker, BANEO_NO_MAS_CONTACTOS)
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock
from fts_web.models import Campana
from fts_daemon.poll_daemon.campana_tracker import CampanaTracker


logger = _logging.getLogger(__name__)


class FinalizacionDeCampanaTests(FTSenderBaseTest):
    """Unit tests de FinalizadorDeCampana"""

    def test_finaliza_campana_baneada_sin_llamada_en_curso(self):
        """Testea que se finalicen campañas que ya no posean contactos,
        cuando dicha campaña no posee llamadas en curso
        """

        campana = Campana(id=1)
        scheduler = RoundRobinTracker()
        scheduler._asterisk_call_status.\
            refrescar_channel_status_si_es_posible = Mock(return_value=None)

        scheduler.real_sleep = Mock(return_value=None)
        scheduler._finalizador_de_campanas = Mock(return_value=None)

        # -----

        scheduler._campana_call_status.banear_campana(campana,
            BANEO_NO_MAS_CONTACTOS)

        scheduler.sleep(20.0)

        scheduler._finalizador_de_campanas.assert_called()
        scheduler.real_sleep.assert_called()

    def test_no_finaliza_campana_baneada_con_llamada_en_curso(self):
        """Testea que NO se finalicen campanas que ya no posean contactos,
        cuando dicha campana posee llamadas en curso.
        """

        campana = Campana(id=1, cantidad_canales=5, cantidad_intentos=1)
        scheduler = RoundRobinTracker()

        scheduler._asterisk_call_status._ami_status_tracker.\
            get_status_por_campana = Mock(return_value={
            1: [
                # int(contacto_id), numero, int(campana_id), int(intentos)
                [2123, 035725551111, 1, 2],
            ]
        })

        scheduler._campana_call_status._crear_tracker = Mock(
            return_value=CampanaTracker(campana))

        scheduler.real_sleep = Mock(return_value=None)
        scheduler._finalizador_de_campanas = Mock(return_value=None)

        # -----

        scheduler._campana_call_status.banear_campana(campana,
            BANEO_NO_MAS_CONTACTOS)

        scheduler.sleep(20.0)

        scheduler._asterisk_call_status._ami_status_tracker.\
            get_status_por_campana.assert_called()
        self.assertFalse(scheduler._finalizador_de_campanas.called)
        scheduler.real_sleep.assert_called()
