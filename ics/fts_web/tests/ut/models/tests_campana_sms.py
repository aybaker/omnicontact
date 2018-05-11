# -*- coding: utf-8 -*-

"""Unittests del modelo CampanaSms"""

from __future__ import unicode_literals

import datetime


from fts_web.models import (CampanaSms, ActuacionSms, OpcionSms)

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


class CampanaReplicarCampana(FTSenderBaseTest):

    def test_replicar_campana_falla_parametro_incorrecto(self):
        campana_sms = OpcionSms(pk=1)

        # -----

        with self.assertRaises(AssertionError):

            CampanaSms.objects.replicar_campana_sms(campana_sms)

    def test_replicar_campana_sms_no_falla(self):
        hora_desde = datetime.time(00, 00)
        hora_hasta = datetime.time(23, 59)

        campana_sms = self.crear_campana_sms()
        respuesta = OpcionSms(respuesta="SI", respuesta_descripcion="afirmativo",
                             campana_sms=campana_sms)
        respuesta.save()

        [self.crea_campana_sms_actuacion_sms(dia_semanal, hora_desde,
            hora_hasta, campana_sms) for dia_semanal in range(0, 4)]

        # -----

        campana_replicada = CampanaSms.objects.replicar_campana_sms(campana_sms)

        self.assertEqual(campana_replicada.estado,
                         CampanaSms.ESTADO_EN_DEFINICION)
        self.assertEqual(OpcionSms.objects.filter(
                         campana_sms=campana_replicada).count(), 1)
        self.assertEqual(ActuacionSms.objects.filter(
                         campana_sms=campana_replicada).count(), 4)
        self.assertEqual(campana_sms.cantidad_chips,
                         campana_replicada.cantidad_chips)
        self.assertEqual(campana_sms.tiene_respuesta,
                         campana_replicada.tiene_respuesta)
        self.assertEqual(campana_sms.template_mensaje,
                         campana_replicada.template_mensaje)
        self.assertEqual(campana_sms.template_mensaje_alternativo,
                         campana_replicada.template_mensaje_alternativo)
        self.assertEqual(campana_sms.template_mensaje_opcional,
                         campana_replicada.template_mensaje_opcional)
