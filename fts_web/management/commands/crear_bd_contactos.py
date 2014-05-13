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


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--cantidad', dest='cantidad', default='100'),
    )

    def handle(self, *args, **options):
        cantidad = int(options['cantidad'])
        print("Iniciando INSERT de {0} contactos...".format(cantidad))
        bd = EventoDeContacto.objects_simulacion.\
            crear_bd_contactos_con_datos_random(cantidad)
        print("INSERT ok - BD: {0}".format(bd.id))
