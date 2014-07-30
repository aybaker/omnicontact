# -*- coding: utf-8 -*-

"""Unittests del modelo GrupoAtencion"""

from __future__ import unicode_literals

import datetime

from django.utils.unittest.case import skipIf
from fts_web.models import Campana, Actuacion, GrupoAtencion, Opcion
from fts_web.tests.utiles import FTSenderBaseTest

from mock import Mock, patch


class EliminarGrupoAtencionTest(FTSenderBaseTest):

    def test_grupo_atencion_puede_borrarse_sin_opciones(self):
        grupo_atencion = GrupoAtencion(id=1)
        grupo_atencion.save = Mock()

        # -----

        self.assertEqual(grupo_atencion.puede_borrarse(), True)

    def test_grupo_atencion_puede_borrarse_campana_borrada(self):
        grupo_atencion = GrupoAtencion(id=1)
        grupo_atencion.save = Mock()

        campana = self.crear_campana_activa()
        campana.estado = Campana.ESTADO_BORRADA
        campana.save()

        self.crea_campana_opcion(0, campana, grupo_atencion=grupo_atencion)

        # -----

        self.assertEqual(grupo_atencion.puede_borrarse(), True)

    def test_grupo_atencion_puede_borrarse_campana_en_definicion(self):
        grupo_atencion = GrupoAtencion(id=1)
        grupo_atencion.save = Mock()

        campana = self.crear_campana_activa()
        campana.estado = Campana.ESTADO_EN_DEFINICION
        campana.save()

        self.crea_campana_opcion(0, campana, grupo_atencion=grupo_atencion)

        # -----

        self.assertEqual(grupo_atencion.puede_borrarse(), True)

    def test_grupo_atencion_puede_borrarse_falla_finalizada(self):
        grupo_atencion = GrupoAtencion(id=1)
        grupo_atencion.save = Mock()

        campana = self.crear_campana_activa()
        campana.finalizar()

        self.crea_campana_opcion(0, campana, grupo_atencion=grupo_atencion)

        # -----

        self.assertEqual(grupo_atencion.puede_borrarse(), False)

    def test_grupo_atencion_puede_borrarse_falla_activa(self):
        grupo_atencion = GrupoAtencion(id=1)
        grupo_atencion.save = Mock()

        campana = self.crear_campana_activa()

        self.crea_campana_opcion(0, campana, grupo_atencion=grupo_atencion)

        # -----

        self.assertEqual(grupo_atencion.puede_borrarse(), False)

    def test_grupo_atencion_borrar(self):
        grupo_atencion = GrupoAtencion(id=1)
        grupo_atencion.save = Mock()

        # -----

        grupo_atencion.borrar()
        self.assertEqual(grupo_atencion.borrado, True)

    def test_grupo_atencion_filtro_de_borrados(self):
        grupo_atencion = GrupoAtencion(id=1)
        grupo_atencion.save = Mock()

        # -----

        grupo_atencion.borrar()

        with self.assertRaises(GrupoAtencion.DoesNotExist):
            GrupoAtencion.objects.get(id=1)
