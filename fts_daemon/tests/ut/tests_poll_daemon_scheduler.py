# -*- coding: utf-8 -*-

"""Tests del modulo fts_daemon.poll_daemon.scheduler"""

from __future__ import unicode_literals

from fts_daemon.poll_daemon.campana_tracker import \
    NoMasContactosEnCampana
from fts_daemon.poll_daemon.scheduler import (
    RoundRobinTracker, CantidadMaximaDeIteracionesSuperada)
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging
from mock import Mock


logger = _logging.getLogger(__name__)


class FinalizacionDeCampanaTests(FTSenderBaseTest):
    """Testea finalizacion de llamadas por parte del scheduler"""

    def test_finaliza_campana_al_terminarse_contactos(self):
        """Testea que se finalicen campanas que ya no posean contactos a
        contactar.
        """

        campana = Campana(id=1)
        campana.finalizar = Mock()

        scheduler = RoundRobinTracker()
        scheduler.max_iterations = 1

        tracker_status = Mock()
        tracker_status.next = Mock(side_effect=NoMasContactosEnCampana)
        tracker_status.limite_alcanzado = Mock(return_value=False)
        tracker_status.campana = campana

        scheduler._finalizar_y_programar_depuracion = Mock(return_value=None)
        scheduler._campana_call_status.obtener_trackers_para_procesar = \
            Mock(return_value=[tracker_status])
        scheduler._asterisk_call_status.\
            refrescar_channel_status_si_es_posible = Mock()
        # -----

        with self.assertRaises(CantidadMaximaDeIteracionesSuperada):
            next(scheduler.generator())

        scheduler._finalizar_y_programar_depuracion.assert_called_once_with(
            campana)
