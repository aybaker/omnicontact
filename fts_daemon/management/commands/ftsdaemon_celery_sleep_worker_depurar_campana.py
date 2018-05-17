# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from fts_daemon.tasks import depurar_campana_async

class Command(BaseCommand):

    def handle(self, *args, **options):
        comando = 'SLEEP_{0}'.format(args[0])
        self.stdout.write("Enviando comando '{0}' a 'depurar_campana_async'"
                          "".format(comando))

        depurar_campana_async(comando)
