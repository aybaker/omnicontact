# -*- coding: utf-8 -*-
"""
Simula intentos para campana existente (si se especifica campana)
o en campana nueva (si se especifica BD).

./virtualenv/bin/python manage.py \
    simular_intentos_de_envios [--campana=ID|--bd=ID]
"""

from __future__ import unicode_literals, print_function

from datetime import date
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand
from fts_daemon.models import EventoDeContacto
from fts_web.models import BaseDatosContacto, Campana
from fts_web.tests.utiles import FTSenderBaseTest


class Tmp(FTSenderBaseTest):
    def runTest(self):
        pass


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--campana', dest='campana', default=''),
        make_option('--bd', dest='bd', default=''),
    )

    def handle(self, *args, **options):
        assert options['campana'] or options['bd'],\
            "Debe especificar --campana o --bd (pero no ambos)"
        assert not (options['campana'] and options['bd']),\
            "Debe especificar --campana o --bd (pero no ambos)"

        settings.FTS_PROGRAMAR_CAMPANA_FUNC = \
            "programar_campana_postgresql"

        if options['campana']:
            campana = Campana.objects.get(pk=options['campana'])
        else:
            id_bd = int(options['bd'])
            test = Tmp()
            campana = test.crear_campana(
                bd_contactos=BaseDatosContacto.objects.get(pk=id_bd),
                fecha_inicio=date.today(), fecha_fin=date.today())
            test.crea_todas_las_opcion_posibles(campana)
            test.crea_todas_las_actuaciones(campana)
            campana.activar()
    
            self.stdout.write('Campaña creada: %s' % campana)

        print("----- Iniciando INSERT de eventos para "
            "campana {0} -----".format(campana.id))
        EventoDeContacto.objects_simulacion.simular_realizacion_de_intentos(
            campana.id)
        print("INSERT ok")

        # Count por evento
        print("----- Cant. de eventos -----")
        [print(x) for x in EventoDeContacto.objects_estadisticas.\
            obtener_count_eventos(campana.id)]

        # Cant. intentos
        print("----- Cant. de intentos -----")
        [print(x) for x in EventoDeContacto.\
            objects_estadisticas.obtener_count_intentos(campana.id)]
