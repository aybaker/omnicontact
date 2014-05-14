# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date
from optparse import make_option
import os
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand
from fts_daemon.asterisk_config import create_dialplan_config_file, \
    reload_config
from fts_daemon.audio_conversor import convertir_audio_de_campana
from fts_web.models import Campana, BaseDatosContacto
from fts_web.tests.utiles import FTSenderBaseTest


os.environ['SKIP_SELENIUM'] = '1'


class Tmp(FTSenderBaseTest):
    def runTest(self):
        pass


def setear_audio(options, campana):
    if options['audio']:
        fd, tmp = tempfile.mkstemp(dir=settings.MEDIA_ROOT, suffix=".wav")
        # Preparamos datos
        tmp_file_obj = os.fdopen(fd, 'w')
        tmp_file_obj.write(
            open(options['audio'], 'r').read()
        )
        tmp_file_obj.flush()

        campana.audio_original = tmp
        campana.save()
        campana = Campana.objects.get(pk=campana.id)
        convertir_audio_de_campana(campana)

    return Campana.objects.get(pk=campana.id)


class Command(BaseCommand):
    args = '<nro_telefonico ...>'
    help = (
        'Crea datos para tests. Args: numeros telefonicos\n'
        ' - Ej: 319751355727335 (para pruebas locales)\n'
        ' - Ej: 10X (para escuchar "hello world" X veces)\n'
    )
    option_list = BaseCommand.option_list + (
        make_option('--audio', action='store', dest='audio', default=None),
        make_option('--bd', dest='bd', default=None),
        make_option('--canales', dest='canales', default='20'),
    )

    def handle(self, *args, **options):
        from django.db import transaction
        with transaction.atomic():
            test = Tmp()
            if len(args):
                numeros_telefonicos = args
            else:
                numeros_telefonicos = [str(x) for x in range(101, 109)]

            cantidad_intentos = os.environ.get('FTS_CANTIDAD_INTENTOS', '1')
            cantidad_intentos = int(cantidad_intentos)

            if options['bd'] is None:
                bd_contactos = test.crear_base_datos_contacto(
                    numeros_telefonicos=numeros_telefonicos)
            else:
                bd_contactos = BaseDatosContacto.objects.get(
                    pk=int(options['bd']))
            campana = test.crear_campana(bd_contactos=bd_contactos,
                fecha_inicio=date.today(), fecha_fin=date.today(),
                cantidad_intentos=cantidad_intentos,
                cantidad_canales=int(options['canales']))

            # Crea opciones y actuaciones...
            test.crea_todas_las_opcion_posibles(campana)
            test.crea_todas_las_actuaciones(campana)

            campana = setear_audio(options, campana)

            campana.activar()
            create_dialplan_config_file()
            reload_config()

            self.stdout.write('Campaña: %s' % campana)
