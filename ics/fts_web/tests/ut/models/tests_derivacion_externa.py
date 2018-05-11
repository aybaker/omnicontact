# -*- coding: utf-8 -*-

"""Unittests del modelo GrupoAtencion"""

from __future__ import unicode_literals

import datetime

from unittest.case import skipIf
from fts_web.models import Campana, Actuacion, DerivacionExterna, Opcion
from fts_web.tests.utiles import FTSenderBaseTest

from mock import Mock, patch


class EliminarDerivacionExternaTest(FTSenderBaseTest):

    def test_derivacion_externa_puede_borrarse_sin_opciones(self):
        derivacion_externa = DerivacionExterna(id=1)
        derivacion_externa.save = Mock()

        # -----

        self.assertEqual(derivacion_externa.puede_borrarse(), True)

    def test_derivacion_externa_puede_borrarse_campana_borrada(self):
        derivacion_externa = DerivacionExterna(id=1)
        derivacion_externa.save = Mock()

        campana = self.crear_campana_activa()
        campana.estado = Campana.ESTADO_BORRADA
        campana.save()

        self.crea_campana_opcion(0, campana,
                                 derivacion_externa=derivacion_externa)

        # -----

        self.assertEqual(derivacion_externa.puede_borrarse(), True)

    def test_derivacion_externa_puede_borrarse_campana_en_definicion(self):
        derivacion_externa = DerivacionExterna(id=1)
        derivacion_externa.save = Mock()

        campana = self.crear_campana_activa()
        campana.estado = Campana.ESTADO_EN_DEFINICION
        campana.save()

        self.crea_campana_opcion(0, campana,
                                 derivacion_externa=derivacion_externa)

        # -----

        self.assertEqual(derivacion_externa.puede_borrarse(), True)

    def test_derivacion_externa_puede_borrarse_falla_finalizada(self):
        derivacion_externa = DerivacionExterna(id=1)
        derivacion_externa.save = Mock()

        campana = self.crear_campana_activa()
        campana.finalizar()

        self.crea_campana_opcion(0, campana, 
                                 derivacion_externa=derivacion_externa)

        # -----

        self.assertEqual(derivacion_externa.puede_borrarse(), False)

    def test_derivacion_externa_puede_borrarse_falla_activa(self):
        derivacion_externa = DerivacionExterna(id=1)
        derivacion_externa.save = Mock()

        campana = self.crear_campana_activa()

        self.crea_campana_opcion(0, campana,
                                 derivacion_externa=derivacion_externa)

        # -----

        self.assertEqual(derivacion_externa.puede_borrarse(), False)

    def test_derivacion_externa_borrar(self):
        derivacion_externa = DerivacionExterna(id=1)
        derivacion_externa.save = Mock()

        # -----

        derivacion_externa.borrar()
        self.assertEqual(derivacion_externa.borrado, True)

    def test_derivacion_externa_filtro_de_borrados(self):
        derivacion_externa = DerivacionExterna(id=1)
        derivacion_externa.save = Mock()

        # -----

        derivacion_externa.borrar()

        with self.assertRaises(DerivacionExterna.DoesNotExist):
            DerivacionExterna.objects.get(id=1)
