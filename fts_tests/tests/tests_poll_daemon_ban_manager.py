# -*- coding: utf-8 -*-

"""Tests generales"""

from __future__ import unicode_literals

from datetime import timedelta
import time

from fts_daemon.poll_daemon.ban_manager import BanManager
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest
import logging as _logging


logger = _logging.getLogger(__name__)


class BanManagerTest(FTSenderBaseTest):

    def test_basico(self):
        bm = BanManager()

        campana_1 = Campana(id=1)
        campana_2 = Campana(id=2)
        campana_3 = Campana(id=3)

        self.assertFalse(bm.esta_baneada(campana_1))
        self.assertFalse(bm.esta_baneada(campana_2))
        self.assertFalse(bm.esta_baneada(campana_3))

        self.assertEquals(bm.get_baneo(campana_1), None)

        # Baneamos 2
        bm.banear_campana(campana_2)

        self.assertFalse(bm.esta_baneada(campana_1))
        self.assertTrue(bm.esta_baneada(campana_2))
        self.assertFalse(bm.esta_baneada(campana_3))

        self.assertEquals(bm.get_baneo(campana_1), None)
        self.assertTrue(bm.get_baneo(campana_2))
        self.assertEquals(bm.get_baneo(campana_2).contador, 1)

        # Baneamos de nuevo 2
        bm.banear_campana(campana_2)

        self.assertFalse(bm.esta_baneada(campana_1))
        self.assertTrue(bm.esta_baneada(campana_2))
        self.assertFalse(bm.esta_baneada(campana_3))

        self.assertEquals(bm.get_baneo(campana_1), None)
        self.assertTrue(bm.get_baneo(campana_2))
        self.assertEquals(bm.get_baneo(campana_2).contador, 2)

        # Des-baneamos
        bm.des_banear(campana_1)
        bm.des_banear(campana_2)
        bm.des_banear(campana_3)

        self.assertFalse(bm.esta_baneada(campana_1))
        self.assertFalse(bm.esta_baneada(campana_2))
        self.assertFalse(bm.esta_baneada(campana_3))

        self.assertEquals(bm.get_baneo(campana_1), None)
        self.assertTrue(bm.get_baneo(campana_2))

        # Re-baneamos campana
        bm.banear_campana(campana_2)

        self.assertFalse(bm.esta_baneada(campana_1))
        self.assertTrue(bm.esta_baneada(campana_2))
        self.assertFalse(bm.esta_baneada(campana_3))

        self.assertEquals(bm.get_baneo(campana_1), None)
        self.assertTrue(bm.get_baneo(campana_2))
        self.assertEquals(bm.get_baneo(campana_2).contador, 3)

        bm.eliminar(campana_1)
        bm.eliminar(campana_2)
        bm.eliminar(campana_3)

        self.assertFalse(bm.esta_baneada(campana_1))
        self.assertFalse(bm.esta_baneada(campana_2))
        self.assertFalse(bm.esta_baneada(campana_3))

    def test_timeout(self):

        class TmpBanManager(BanManager):
            def get_timedelta_baneo(self):
                return timedelta(seconds=0.1)

        bm = TmpBanManager()
        campana_1 = Campana(id=1)
        self.assertFalse(bm.esta_baneada(campana_1))
        bm.banear_campana(campana_1)

        # en una maquina lenta, el siguiente assert puede fallar
        self.assertTrue(bm.esta_baneada(campana_1))
        time.sleep(0.1)
        self.assertFalse(bm.esta_baneada(campana_1))

    def test_ban_forever(self):

        class TmpBanManager(BanManager):
            def get_timedelta_baneo(self):
                return timedelta(seconds=0.1)

        bm = TmpBanManager()
        campana_1 = Campana(id=1)
        self.assertFalse(bm.esta_baneada(campana_1))
        bm.banear_campana(campana_1, forever=True)

        # en una maquina lenta, el siguiente assert puede fallar
        self.assertTrue(bm.esta_baneada(campana_1))
        time.sleep(0.15)
        self.assertTrue(bm.esta_baneada(campana_1))

    def test_razon(self):
        bm = BanManager()
        campana_1 = Campana(id=1)
        campana_2 = Campana(id=2)
        campana_3 = Campana(id=3)
        bm.banear_campana(campana_1, "A")
        bm.banear_campana(campana_2, "B")
        bm.banear_campana(campana_3, "A")

        razon_a = bm.obtener_por_razon("A")
        self.assertEqual(len(razon_a), 2)
        self.assertIn(campana_1, razon_a)
        self.assertIn(campana_3, razon_a)
