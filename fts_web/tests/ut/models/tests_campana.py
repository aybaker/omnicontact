# -*- coding: utf-8 -*-

"""Unittests del modelo Campana"""

from __future__ import unicode_literals

import datetime

from django.utils.unittest.case import skipIf
from fts_web.models import Campana, Actuacion
from fts_web.tests.utiles import FTSenderBaseTest


class ObtenerVencidasParaFinalizarTest(FTSenderBaseTest):
    """Clase para testear Campana.objects.obtener_vencidas_para_finalizar()"""

    def test_devuelve_vieja(self):
        """Testea que devuelve campana con fecha_fin pasada"""
        bd = self.crear_base_datos_contacto(2)
        self.crear_campana_activa(bd_contactos=bd, cantidad_canales=1)

        # Campaña vieja, finalizó hace mucho
        campana_vieja = self.crear_campana_activa(bd_contactos=bd,
                                                  cantidad_canales=1)
        campana_vieja.fecha_inicio = datetime.datetime(2001, 01, 01).date()
        campana_vieja.fecha_fin = datetime.datetime(2001, 01, 01).date()
        campana_vieja.save()

        self.assertEquals(Campana.objects.count(), 2)

        # ---

        campanas = list(Campana.objects.obtener_vencidas_para_finalizar())

        self.assertEqual(len(campanas), 1)
        self.assertEqual(campanas[0].id, campana_vieja.id)

    def test_devuelve_de_hoy_sin_actuacion(self):
        now = datetime.datetime.now()

        bd = self.crear_base_datos_contacto(2)
        self.crear_campana_activa(bd_contactos=bd, cantidad_canales=1)

        # Camp. q' finaliza hoy pero NO posee actuacion para hoy
        campana_a_finalizar = self.crear_campana_activa(bd_contactos=bd,
                                                        cantidad_canales=1)
        campana_a_finalizar.fecha_inicio = datetime.datetime(2001, 01, 01).\
            date()
        campana_a_finalizar.fecha_fin = now.date()
        campana_a_finalizar.save()

        weekday = now.weekday() - 1
        if weekday == -1:
            weekday = 6

        Actuacion.objects.create(campana=campana_a_finalizar,
            dia_semanal=weekday,
            hora_desde=datetime.time(1, 0),
            hora_hasta=datetime.time(2, 0)
        )

        self.assertEquals(Campana.objects.count(), 2)

        # ---

        campanas = list(Campana.objects.obtener_vencidas_para_finalizar())

        self.assertEqual(len(campanas), 1)
        self.assertEqual(campanas[0].id, campana_a_finalizar.id)

    def test_devuelve_de_hoy_con_actuaciones_vencidas(self):
        now = datetime.datetime.now()

        bd = self.crear_base_datos_contacto(2)
        self.crear_campana_activa(bd_contactos=bd, cantidad_canales=1)

        # Campaña q' finaliza HOY, con Actuacion para hoy (pero vencida)
        campana_a_finalizar = self.crear_campana_activa(bd_contactos=bd,
                                                        cantidad_canales=1)
        campana_a_finalizar.fecha_inicio = datetime.datetime(2001, 01, 01).\
            date()
        campana_a_finalizar.fecha_fin = now.date()
        campana_a_finalizar.save()

        Actuacion.objects.create(campana=campana_a_finalizar,
            dia_semanal=now.weekday(),
            hora_desde=datetime.time(0, 0),
            hora_hasta=datetime.time(0, 1)
        )

        # Campaña con actuacion! No deberia ser devuelta
        campana_a_ejecutar = self.crear_campana_activa(bd_contactos=bd,
                                                       cantidad_canales=1)
        campana_a_ejecutar.fecha_inicio = datetime.datetime(2001, 01, 01).\
            date()
        campana_a_ejecutar.fecha_fin = now.date()
        campana_a_ejecutar.save()

        Actuacion.objects.create(campana=campana_a_ejecutar,
            dia_semanal=now.weekday(),
            hora_desde=datetime.time(23, 58),
            hora_hasta=datetime.time(23, 59)
        )

        self.assertEquals(Campana.objects.count(), 3)

        # ---

        campanas = list(Campana.objects.obtener_vencidas_para_finalizar())

        self.assertEqual(len(campanas), 1)
        self.assertEqual(campanas[0].id, campana_a_finalizar.id)

    @skipIf(True, "Falta implementar")
    def test_devuelve_de_manana_sin_actuaciones(self):
        # FIXME: implementar tests y funcionalidad!
        pass
