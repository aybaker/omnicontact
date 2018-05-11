# -*- coding: utf-8 -*-
"""
Simula intentos para campana existente (si se especifica campana)
o en campana nueva (si se especifica BD).

./virtualenv/bin/python manage.py \
    simular_intentos_de_envios [--campana=ID|--bd=ID]
"""

from __future__ import unicode_literals, print_function

from optparse import make_option
import pprint

from django.core.management.base import BaseCommand
from fts_daemon.models import EventoDeContacto
from fts_web.models import Campana
from fts_web.tests.utiles import FTSenderBaseTest


class Tmp(FTSenderBaseTest):
    def runTest(self):
        pass


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--campana', dest='campana', default=''),
        make_option('--full', dest='full', action='store_true', default=False),
    )

    def handle(self, *args, **options):
        campana = Campana.objects.get(pk=options['campana'])

        #======================================================================
        # obtener_count_eventos
        #======================================================================
        counts = EventoDeContacto.objects_estadisticas.obtener_count_eventos(
            campana.id)
        print("----- Count de eventos -----")
        for evento_id, evento_count in counts:
            print("{0} ({1}): {2}".format(
                EventoDeContacto.objects.get_nombre_de_evento(evento_id),
                evento_id, evento_count))
        print("")

        #======================================================================
        # obtener_count_intentos
        #======================================================================
        counts = EventoDeContacto.objects_estadisticas.obtener_count_intentos(
            campana.id)
        print("----- Count de intentos -----")
        for cant_int, count in counts:
            print("{0} contactos fueron intentados {1} veces".format(
                cant_int, count))
        print("")

        #======================================================================
        # obtener_estadisticas_de_campana
        #======================================================================
        counter_x_estado, counter_intentos, counter_por_evento = \
            EventoDeContacto.objects_estadisticas.\
            obtener_estadisticas_de_campana(campana.id)

        print("----- Estadisticas / counter_x_estado-----")
        print("finalizado_x_evento_finalizador: {0}".format(
            counter_x_estado['finalizado_x_evento_finalizador']))
        print("finalizado_x_limite_intentos: {0}".format(
            counter_x_estado['finalizado_x_limite_intentos']))
        print("pendientes: {0}".format(counter_x_estado['pendientes']))
        print("----- Estadisticas / counter_intentos -----")
        for key in sorted(counter_intentos):
            print("{0} contactos fueron intentados {1} veces".format(
                counter_intentos[key], key))
        print("----- Estadisticas / counter_por_evento -----")
        for key in sorted(counter_por_evento):
            print("Evento {0}: {1} veces".format(
                EventoDeContacto.objects.get_nombre_de_evento(key),
                counter_por_evento[key]))
        print("")

        #======================================================================
        # obtener_array_eventos_por_contacto
        #======================================================================
        if options['full']:
            resultado = EventoDeContacto.objects_estadisticas.\
                obtener_array_eventos_por_contacto(campana.id)
            print("----- Eventos x contacto -----")
            for contacto_id, eventos, _ in resultado:
                print("{0}: {1}".format(contacto_id, pprint.pformat(eventos)))
            print("")
