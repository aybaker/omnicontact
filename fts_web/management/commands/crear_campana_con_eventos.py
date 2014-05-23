# -*- coding: utf-8 -*-

"""

Crea una campaña con eventos de distintos tipo.

./virtualenv/bin/python manage.py \
    crear_campana_con_eventos --bd=ID
"""

from __future__ import unicode_literals, print_function

from datetime import date
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from fts_daemon.models import EventoDeContacto
from fts_web.models import BaseDatosContacto
from fts_web.tests.utiles import FTSenderBaseTest


class Tmp(FTSenderBaseTest):
    def runTest(self):
        pass


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--bd', dest='bd', default=''),
    )

    def handle(self, *args, **options):
        assert options['bd'], "Debe especificar --bd"
        test = Tmp()
        id_bd = int(options['bd'])

        # Forzamos uso de funciones para PostgreSql
        settings.FTS_PROGRAMAR_CAMPANA_FUNC = \
            "_programar_campana_postgresql"

        print("----- Creando campana...")
        campana = test.crear_campana(
            bd_contactos=BaseDatosContacto.objects.get(pk=id_bd),
            fecha_inicio=date.today(), fecha_fin=date.today(),
            cantidad_intentos=3)

        # Crea opciones y actuaciones...
        test.crea_todas_las_opcion_posibles(campana)
        test.crea_todas_las_actuaciones(campana)

        print("----- Activando campana {0}", campana.id)
        campana.activar()

        print("----- Simula intentos de contactos")
        EventoDeContacto.objects_simulacion.simular_realizacion_de_intentos(
            campana.id, intento=1)
        print("-- Mas...")
        EventoDeContacto.objects_simulacion.simular_realizacion_de_intentos(
            campana.id, intento=2)
        print("-- Mas...")
        EventoDeContacto.objects_simulacion.simular_realizacion_de_intentos(
            campana.id, intento=3)
        print("INSERTs ok")

        print("----- Simula eventos finalizadores")
        # Inserta eventos "finalizadores". No es TAN inteligente, ya que
        # puede insertar eventos "finalizadores" para contactos que nunca
        # fueron procesados, pero bueno... «todavía sirve, todavía sirve»
        EventoDeContacto.objects_simulacion.simular_evento(campana.id, 3,
            EventoDeContacto.objects.get_eventos_finalizadores()[0],
            0.1)
        print("INSERTs ok")
