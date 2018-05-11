# -*- coding: utf-8 -*-

"""
"""

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
    if not options['audio']:
        return campana

    fd, tmp = tempfile.mkstemp(dir=settings.MEDIA_ROOT, suffix=".wav")
    # Preparamos datos
    tmp_file_obj = os.fdopen(fd, 'w')
    tmp_file_obj.write(
        open(options['audio'], 'r').read()
    )
    tmp_file_obj.flush()

    audios_de_campana = campana.audios_de_campana.all()
    for audio_de_campana in (audios_de_campana[0], audios_de_campana[4]):
        assert audio_de_campana.audio_original, \
            ("Al parecer, la instancia de AudioDeCampana no posee un "
             "archivo asociado (seguramente es un AudioDeCampana de tipo TTS)")

        solo_nombre_de_archivo = os.path.split(tmp)[1]
        audio_de_campana.audio_original = solo_nombre_de_archivo
        audio_de_campana.audio_asterisk = ''
        audio_de_campana.save()
        convertir_audio_de_campana(audio_de_campana)

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
        make_option('--intentos', dest='intentos', default='1'),
    )

    def handle(self, *args, **options):
        from django.db import transaction
        with transaction.atomic(savepoint=False):
            test = Tmp()
            if len(args):
                numeros_telefonicos = args
            else:
                numeros_telefonicos = [str(x) for x in range(101, 109)]

            if options['bd'] is None:
                bd_contactos = test.crear_base_datos_contacto(
                    numeros_telefonicos=numeros_telefonicos)
            else:
                bd_contactos = BaseDatosContacto.objects.get(
                    pk=int(options['bd']))

            campana = test.crear_campana(bd_contactos=bd_contactos,
                fecha_inicio=date.today(), fecha_fin=date.today(),
                cantidad_intentos=int(options['intentos']),
                cantidad_canales=int(options['canales']),
            )

            # Crea opciones y actuaciones...
            test.crea_todas_las_opcion_posibles(campana)
            test.crea_todas_las_actuaciones(campana)

            campana = setear_audio(options, campana)

            campana.activar()
            create_dialplan_config_file()
            reload_config()

            self.stdout.write('Campaña: %s' % campana)
