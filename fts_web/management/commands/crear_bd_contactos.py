# -*- coding: utf-8 -*-
"""
Crea BD de contactos con muchos contactos.

./virtualenv/bin/python manage.py \
    crear_bd_contactos \
    --cantidad="$( echo $(( $RANDOM * $RANDOM )) | cut -c 1-5)"
"""

from __future__ import unicode_literals, print_function

from optparse import make_option

from django.core.management.base import BaseCommand
from fts_daemon.models import EventoDeContacto
from django.conf import settings


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--cantidad', dest='cantidad', default='100'),
        make_option('--force-debug', dest='force_debug', action="store_true",
            default=False),
    )

    def handle(self, *args, **options):
        cantidad = int(options['cantidad'])
        if options['force_debug']:
            settings.DEBUG = True
        print("Iniciando INSERT de {0} contactos...".format(cantidad))
        bd = EventoDeContacto.objects_simulacion.\
            crear_bd_contactos_con_datos_random(cantidad)
        print("INSERT ok - BD: {0}".format(bd.id))

        bd.get_metadata().validar_metadatos()
