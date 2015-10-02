# -*- coding: utf-8 -*-

"""Unittests del modelo CampanaSms"""

from __future__ import unicode_literals

import datetime


from fts_web.models import (CampanaSms, Actuacion)

from fts_web.tests.utiles import FTSenderBaseTest


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