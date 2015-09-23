# -*- coding: utf-8 -*-

"""Tests para el form CampanaSmsForm"""

from __future__ import unicode_literals

import datetime

from django.conf import settings
from fts_web.forms import CampanaSmsForm
from fts_web.tests.utiles import FTSenderBaseTest


class CreateCampanaSmsFormTest(FTSenderBaseTest):
    """
    Estos tests corresponden al form de CampanaSmsForm
    """
    def test_create_campana_sms_cantidad_chips_mayor_falla(self):
        """
        Este test crea una campana sms con cantidad de chips mayor a la
        contratada
        """
        bd_contacto = self.crear_base_datos_contacto()
        data = {
            'nombre': 'Test Prueba campana sms',
            'cantidad_chips': settings.FTS_LIMITE_GLOBAL_DE_CHIPS + 1,
            'fecha_inicio': datetime.datetime.now(),
            'fecha_fin': datetime.datetime.now(),
            'bd_contacto': bd_contacto.pk,
            'tiene_respuesta': True,
        }
        campana_sms_form = CampanaSmsForm(data)
        self.assertFalse(campana_sms_form.is_valid())
        self.assertEqual(campana_sms_form.errors, {
            'cantidad_chips': ["Ha excedido el limite de cantitad de modems. "
                               "Su cantidad de modems contratado es {0}".format(
                                settings.FTS_LIMITE_GLOBAL_DE_CHIPS)],
        })

    def test_create_campana_cantidad_chips_menor(self):
        """
        Este test crea una campana sms con cantidad de chips menor a la
        contratada
        """
        bd_contacto = self.crear_base_datos_contacto()
        data = {
            'nombre': 'Test Prueba campana sms',
            'cantidad_chips': settings.FTS_LIMITE_GLOBAL_DE_CHIPS - 1,
            'fecha_inicio': datetime.datetime.now(),
            'fecha_fin': datetime.datetime.now(),
            'bd_contacto': bd_contacto.pk,
            'tiene_respuesta': True,
        }
        campana_sms_form = CampanaSmsForm(data)
        self.assertTrue(campana_sms_form.is_valid())

    def test_create_campana_cantidad_chips_igual(self):
        """
        Este test crea una campana sms con cantidad de chips igual a la
        contratada
        """
        bd_contacto = self.crear_base_datos_contacto()
        data = {
            'nombre': 'Test Prueba campana sms',
            'cantidad_chips': settings.FTS_LIMITE_GLOBAL_DE_CHIPS,
            'fecha_inicio': datetime.datetime.now(),
            'fecha_fin': datetime.datetime.now(),
            'bd_contacto': bd_contacto.pk,
            'tiene_respuesta': True,
        }
        campana_sms_form = CampanaSmsForm(data)
        self.assertTrue(campana_sms_form.is_valid())
