# -*- coding: utf-8 -*-

from random import randint

from django.core.management.base import BaseCommand, CommandError
from ominicontacto_app.tests.factories import (GrabacionFactory, GrabacionMarcaFactory,
                                               AgenteProfileFactory)


class Command(BaseCommand):
    """
    Crea tantas grabaciones como se especifique en el parametro, son marcadas o no, aleatoriamente
    """

    help = u'Crea la cantidad de grabaciones de acuerdo al parámetro recibido'

    def add_arguments(self, parser):
        parser.add_argument('nro_llamadas', nargs=1, type=int)

    def grabacion_marcada_aleatoria(self, agente):
        """
        Crea un marca de grabación
        """
        grabacion = GrabacionFactory.create(agente=agente)
        crear_grabacion_marcada = bool(randint(0, 1))

        if crear_grabacion_marcada:
            GrabacionMarcaFactory.create(uid=grabacion.uid)

    def handle(self, *args, **options):
        nro_grabaciones = options['nro_llamadas'][0]
        agente = AgenteProfileFactory.create()
        for i in range(nro_grabaciones):
            try:
                self.grabacion_marcada_aleatoria(agente)
            except Exception as e:
                raise CommandError('Fallo del comando: {0}'.format(e.message))
        self.stdout.write(
            self.style.SUCCESS('Creada(s) {0} grabaciones(s)'.format(nro_grabaciones)))
