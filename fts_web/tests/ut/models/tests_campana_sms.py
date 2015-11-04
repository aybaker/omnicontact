# -*- coding: utf-8 -*-

"""Unittests del modelo CampanaSms"""

from __future__ import unicode_literals

import datetime


from fts_web.models import (CampanaSms, Actuacion)

from fts_web.tests.utiles import FTSenderBaseTest
from mock import Mock


class MetodosValidadoresDeCampanaSmsTest(FTSenderBaseTest):

    def test_campana_valida_mensaje_falla_sin_template_mensaje(self):
        campana_sms = CampanaSms.objects.create(cantidad_chips=3,
                                            tiene_respuesta=False,
                                            identificador_campana_sms=1)

        self.assertEqual(campana_sms.valida_mensaje(), False)

    def test_campana_valida_mensaje(self):
        campana_sms = CampanaSms.objects.create(cantidad_chips=3,
                                                template_mensaje="test mensaje",
                                            tiene_respuesta=False,
                                            identificador_campana_sms=1)

        self.assertEqual(campana_sms.valida_mensaje(), True)


class EliminarCampanaSmsTest(FTSenderBaseTest):

    def test_campana_sms_puede_borrarse_falla(self):
        campana_sms = CampanaSms(id=1)
        campana_sms.save = Mock()
        campana_sms.estado = CampanaSms.ESTADO_CONFIRMADA

        # -----

        self.assertEqual(campana_sms.puede_borrarse(), False)

    def test_campana_sms_puede_borrarse(self):
        campana_sms = CampanaSms(id=1)
        campana_sms.save = Mock()
        campana_sms.estado = CampanaSms.ESTADO_PAUSADA

        # -----

        self.assertEqual(campana_sms.puede_borrarse(), True)

    def test_campana_sms_borrar_falla_con_estado_finalizada(self):
        campana_sms = CampanaSms(id=1)
        campana_sms.save = Mock()
        campana_sms.estado = CampanaSms.ESTADO_CONFIRMADA

        # -----
        self.assertRaises(AssertionError, campana_sms.borrar)

    def test_campana_sms_borrar_con_estado_depurada(self):
        campana_sms = CampanaSms(id=1)
        campana_sms.save = Mock()
        campana_sms.estado = CampanaSms.ESTADO_PAUSADA

        # -----
        campana_sms.borrar()
        self.assertEqual(campana_sms.estado, CampanaSms.ESTADO_BORRADA)

    def test_campana_sms_filtro_de_borradas(self):
        campana_sms = CampanaSms(id=1)
        campana_sms.save = Mock()
        campana_sms.estado = CampanaSms.ESTADO_PAUSADA

        # -----
        campana_sms.borrar()

        with self.assertRaises(CampanaSms.DoesNotExist):
            CampanaSms.objects.get(id=1)
