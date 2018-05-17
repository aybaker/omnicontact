# -*- coding: utf-8 -*-

"""Metodos utilitarios para ser reutilizados en los distintos
módulos de tests.

ATENCION: aqui NO estan los tests del paquete 'fts_tests.utiles',
sino que estan los metodos utilitarios para facilitar el
desarrollo de los tests.
"""

from __future__ import unicode_literals

import pprint

from fts_daemon.models import EventoDeContacto


class EventoDeContactoAssertUtilesMixin(object):

    def _get_logger(self):
        raise NotImplementedError()

    # Python 2.x no soporta agregar checks={}
    def _assertCountEventos(self, campana, *args, **kwargs):
        """Asegura que `obtener_count_eventos()` devuelve los
        tipos de eventos pasados por parametros, y solo esos:

        Ejemplos:

        1. _assertCountEventos(campana, 1, 2): asegura que
           obtener_count_eventos() devuelve solo eventos 1 y 2.

        2. _assertCountEventos(campana, 1, 2, checks={1: 73}):
           asegura que obtener_count_eventos() devuelve solo eventos
           1 y 2, y que ha contado 73 eventos del tipo '1'.
        """
        checks = kwargs.get('checks', {})
        counts = dict(EventoDeContacto.objects_estadisticas.\
            obtener_count_eventos(campana.id))
        self._get_logger().info("obtener_count_eventos() %s",
            pprint.pformat(counts))
        for ev_id in args:
            self.assertTrue(ev_id in counts,
                "obtener_count_eventos() no devolvio count "
                "para evento {0} ({1})".format(ev_id,
                    EventoDeContacto.objects.get_nombre_de_evento(ev_id)))

        self.assertTrue(len(counts) == len(args))
        for key in checks:
            self.assertEquals(checks[key], counts[key])
        return counts

    def _assertArrayEventos(self, campana, *args):
        """Asegura que `obtener_array_eventos_por_contacto()` devuelve los
        tipos de eventos pasados por parametros, y solo esos:

        Ejemplos:

        1. _assertArrayEventos(campana, 1, 2): asegura que
           obtener_array_eventos_por_contacto() devuelve contactos con
           eventos 1 y 2.
        """
        array_eventos = EventoDeContacto.objects_estadisticas.\
            obtener_array_eventos_por_contacto(campana.id)
        eventos = set()
        for item in array_eventos:
            # item[0] -> contact_id
            # item[1] -> ARRAY
            # item[2] -> timestamp
            eventos.update(set(item[1]))

        self.assertEquals(len(eventos), len(args))
        self.assertEquals(eventos, set(args))

    def _assertPendientes(self, campana, cant_pendientes, *args):
        """Asegura que `obtener_pendientes()` devuelve los
        id_contacto correctos. En `*args` se reciben las cantidades
        de intentos que se deberian encontrar.

        Si *cant_pendientes* != None, controla que se devuelva esa
        cantidad de pendientes.

        Ejemplos:

        1. _assertPendientes(campana, 4241, 0, 1, 2): asegura que se
        encontraron 4241 pendientes, y que entre los pendientes hay
        algunos q' se intentaron 0 veces, 1 vez y 2 veces.
        """
        pendientes = EventoDeContacto.objects_gestion_llamadas.\
            obtener_pendientes(campana.id)
        if cant_pendientes is not None:
            self.assertEquals(len(pendientes), cant_pendientes)

        # cp: contacto pendiente
        self.assertEquals(set([cp.cantidad_intentos_realizados
                               for cp in pendientes]),
                          set(args)
                          )

        return pendientes

    def _assertCountIntentos(self, campana, *args):
        """Asegura que `obtener_count_intentos()` devuelve los
        counts de intentos correctos. En `*args` se reciben las cantidades
        de intentos que se deberian encontrar.

        Ejemplos:

        1. _assertCountIntentos(campana, 1, 2): asegura que se
        encontraron contactos q' se intentaron 1 vez y 2 veces.
        """
        info = EventoDeContacto.objects_estadisticas.obtener_count_intentos(
            campana.id)
        self.assertEquals(len(info), len(args))
        self.assertEquals(set([row[0] for row in info]), set(args))

    def dump_count_eventos(self, campana):
        counts = EventoDeContacto.objects_estadisticas.\
            obtener_count_eventos(campana.id)
        print("---------- dump_count_eventos() ----------")
        for id_ev, count in counts:
            print("{0}: {1}".format(
                EventoDeContacto.objects.get_nombre_de_evento(id_ev), count))
        print("------------------------------------------")
