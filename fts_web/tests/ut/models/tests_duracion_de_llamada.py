# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

from django.test.testcases import TestCase
from mock import Mock, create_autospec

from fts_web.tests.utiles import FTSenderBaseTest
from fts_web.models import Campana, DuracionDeLlamada


class ObtenerDuracionDeLlamadaTest(FTSenderBaseTest):
    """
    Unit Test del método
    DuracionDeLlamadaManager.objects.obtener_duracion_de_llamdas()
    """

    def test_devuleve_datos_correctos(self):
        for i in range(1, 5):
            campana = Campana(pk=i)

            duracion_de_llamada = DuracionDeLlamada(
                pk=i, campana=campana, numero_telefono='3513368309',
                fecha_hora_llamada=datetime.datetime.now(),
                duracion_en_segundos=i)
            duracion_de_llamada.save()

        # -----

        datos = DuracionDeLlamada.objects.obtener_duracion_de_llamdas(
            '3513368309')

        self.assertEqual(len(datos), 4)

        for i, dato in enumerate(datos):
            self.assertEqual(dato.pk, i+1)
            self.assertEqual(dato.numero_telefono, '3513368309')
            self.assertEqual(dato.duracion_en_segundos, i+1)

    def test_devuelve_queryset_vacio_con_numero_telefono_inexistente(self):
        for i in range(1, 5):
            campana = Campana(pk=i)

            duracion_de_llamada = DuracionDeLlamada(
                pk=i, campana=campana, numero_telefono='3513368309',
                fecha_hora_llamada=datetime.datetime.now(),
                duracion_en_segundos=i)
            duracion_de_llamada.save()

        # -----

        datos = DuracionDeLlamada.objects.obtener_duracion_de_llamdas(
            '3513333333')

        self.assertEqual(len(datos), 0)

    def test_devuelve_queryset_vacio_con_numero_telefono_invalido(self):
        for i in range(1, 5):
            campana = Campana(pk=i)

            duracion_de_llamada = DuracionDeLlamada(
                pk=i, campana=campana, numero_telefono='3513368309',
                fecha_hora_llamada=datetime.datetime.now(),
                duracion_en_segundos=i)
            duracion_de_llamada.save()

        # -----

        datos = DuracionDeLlamada.objects.obtener_duracion_de_llamdas(
            '3513test')

        self.assertEqual(len(datos), 0)
