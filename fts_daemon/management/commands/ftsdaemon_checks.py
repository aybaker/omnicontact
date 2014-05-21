# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import os
import subprocess

from django.conf import settings
from django.core.management.base import BaseCommand
from fts_daemon.asterisk_config import create_queue_config_file, \
    create_dialplan_config_file
from fts_daemon.audio_conversor import convertir_audio
from fts_web.models import Campana
from fts_web import version


AUDIO_FILE = "test/wavs/8k16bitpcm.wav"

OUTPUT_FILENAME = "/tmp/ftsdaemon_check_audio_conversor{0}"


class Command(BaseCommand):

    def handle(self, *args, **options):

        logger = logging.getLogger()
        [logger.removeHandler(x) for x in logger.handlers]

        self.stdout.write('Iniciando chequeos - Ver.: {0} - {1} - {2}'.format(
            version.FTSENDER_COMMIT, version.FTSENDER_AUTHOR,
            version.FTSENDER_BUILD_DATE))

        # NTP
        self.stdout.write('Chequeando NTP...')
        retcode = subprocess.call('ntpstat > /dev/null 2> /dev/null',
            shell=True)
        if retcode == 0:
            self.stdout.write(' + OK')
        else:
            self.stdout.write(' + ERROR: ntpstat ha devuelto {0}'.format(
                retcode))

        # BD
        self.stdout.write('Chequeando acceso a BD...')
        Campana.objects.exists()
        self.stdout.write(' + OK')

        # Reload queues de Asterisk
        self.stdout.write('Chequeando create_queue_config_file()...')
        create_queue_config_file()
        self.stdout.write(' + OK')

        # Reload dialplan de Asterisk
        self.stdout.write('Chequeando create_dialplan_config_file()...')
        create_dialplan_config_file()
        self.stdout.write(' + OK')

        # Conversor de audio
        audio = os.path.dirname(__file__)
        audio = os.path.abspath(audio)
        audio = os.path.join(audio, "../../..")
        audio = os.path.join(audio, AUDIO_FILE)
        assert os.path.exists(audio)
        self.stdout.write('Chequeando convertir_audio()...')
        output = OUTPUT_FILENAME.format(
            settings.TMPL_FTS_AUDIO_CONVERSOR_EXTENSION)
        if os.path.exists(output):
            os.unlink(output)
        convertir_audio(audio, output)
        if os.path.exists(output):
            self.stdout.write(' + OK')
        else:
            self.stdout.write(' + ERROR: no se encontro archivo de salida')
