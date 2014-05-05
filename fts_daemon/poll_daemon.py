# -*- coding: utf-8 -*-
"""
Daemon que busca pendientes y realiza envios.
"""

from __future__ import unicode_literals

from datetime import datetime, timedelta
import os
import random
import time

from django.conf import settings
from fts_daemon.llamador_contacto import procesar_contacto
from fts_web.models import Campana, EventoDeContacto
import logging as _logging


#
# Import settings & models ^ALLA ARRIBA^ to force setup of Django
#
# Seteamos nombre, sino al ser ejecutado via uWSGI
#  el logger se llamara '__main__'
logger = _logging.getLogger('fts_daemon.poll_daemon')


class CampanaNoEnEjecucion(Exception):
    """Marca cancelacion de procesamiento de campaña,
    ya sea porque está pausada, no esta en rango de fecha de campaña,
    o en rango de horas de actuaciones
    """


class NoMasContactosEnCampana(Exception):
    """No se encontraron contactos por procesar para la campaña.
    """


class NoHayCampanaEnEjecucion(Exception):
    """No se encontraron campanas en ejecucion.
    """


class CampanaTracker(object):

    def __init__(self, campana):
        self.cache = []
        self.campana = campana
        self.actuacion = None
        self.generator = None
        self.fetch_min = 20
        self.fetch_max = 100

    def _get_fetch(self):
        return random.randint(self.fetch_min, self.fetch_max)

    def _populate_cache(self):
        """Guarda datos a devolver en `self.cache`.

        Raises:
        - NoMasContactosEnCampana: si no hay mas llamados pendientes
        """
        if not self.campana.verifica_fecha(datetime.now()):
            raise CampanaNoEnEjecucion()

#        self.actuacion = self.campana.obtener_actuacion_actual()
#        if not self.actuacion:
#            logger.info("Cancelando xq no hay actuacion activa para "
#                "campana %s", self.campana.id)
#            raise CampanaNoEnEjecucion()

        contactos_values = EventoDeContacto.objects_gestion_llamadas.\
            obtener_pendientes(self.campana.id,
                limit=self._get_fetch())

        if not contactos_values:
            raise NoMasContactosEnCampana()

        id_contacto_y_telefono = EventoDeContacto.objects_gestion_llamadas.\
            obtener_datos_de_contactos([tmp[1] for tmp in contactos_values])

        self.cache = [(self.campana, contacto_id, telefono)
            for contacto_id, telefono in id_contacto_y_telefono]

    def next(self):
        """Devuelve datos de contacto a contactar:
        (campana, contacto_id, telefono)

        Raises:
        - CampanaNoEnEjecucion
        - NoMasContactosEnCampana
        """
        if self.generator is None:
            self.generator = self.get_generator()
        return next(self.generator)

    def get_generator(self):
        """Devuelve datos de contacto a contactar:
        (campana, contacto_id, telefono)

        Raises:
        - CampanaNoEnEjecucion
        - NoMasContactosEnCampana
        """
        while True:

            # Fecha actual local.
            hoy_ahora = datetime.now()

            # Esto quiza no haga falta, porque en teoria
            # el siguiente control de actuacion detectara el
            # cambio de dia, igual hacemos este re-control
            if not self.campana.verifica_fecha(hoy_ahora):
                raise CampanaNoEnEjecucion()

#            if not self.actuacion.verifica_actuacion(hoy_ahora):
#                raise CampanaNoEnEjecucion()

            # FIXME: chequear q' el estado sea VALIDO, o sea,
            #  que no este pausada, pero tampoco finalizada, etc.
            # Valida que la campana no se haya pausado.
            if Campana.objects.verifica_estado_pausada(self.campana.pk):
                raise CampanaNoEnEjecucion()

            if not self.cache:
                self._populate_cache()  # -> NoMasContactosEnCampana

            yield self.cache.pop(0)


class RoundRobinTracker(object):

    def __init__(self):
        self.trackers_campana = {}
        """dict(): Campana -> CampanaTracker"""

        self.campanas_baneadas = {}
        """dict(): Campana -> datetime (hasta el momento que esta
        baneado"""

        self.cache = []
        self.iter_count = 0
        self.espera_sin_campanas = 2

    def _get_timedelta_baneo(self):
        return timedelta(minutes=1)

    def _banear_campana(self, campana):
        self.campanas_baneadas[campana] = datetime.now() + \
            self._get_timedelta_baneo()

    def _esta_baneada(self, campana):
        if not campana in self.campanas_baneadas:
            return False

        baneada_hasta = self.campanas_baneadas[campana]
        if datetime.now() < baneada_hasta:
            return True
        else:
            del self.campanas_baneadas[campana]
            return False

    def _update_trackers_campana(self):
        """Raises:
        - NoHayCampanaEnEjecucion
        """
        self.iter_count += 1
        if self.iter_count <= 10:
            return

        # Reseteamos y refrescamos
        self.iter_count = 0

        old_trackers = dict(self.trackers_campana)
        new_trackers = {}
        for campana in Campana.objects.obtener_ejecucion():

            if self._esta_baneada(campana):
                continue

            if campana in old_trackers:
                # Ya existia de antes, la mantenemos
                new_trackers[campana] = old_trackers[campana]
                del old_trackers[campana]
            else:
                # Es nueva
                new_trackers[campana] = CampanaTracker(campana)

        self.trackers_campana = new_trackers

        # Logueamos campanas q' no van mas...
        for campana in old_trackers:
            logger.info("Ya no esta mas trackeada la campana %s",
                campana.id)

        # Luego de procesar y loguear todo, si vemos q' no hay campanas
        # ejecucion, lanzamos excepcion
        if not self.trackers_campana:
            # No se encontraron campanas en ejecucion
            raise NoHayCampanaEnEjecucion()

    def generator(self):
        while True:
            dict_copy = dict(self.trackers_campana)
            for campana, tracker_campana in dict_copy.iteritems():
                try:
                    yield tracker_campana.next()
                except CampanaNoEnEjecucion:
                    self._banear_campana(campana)
                    logger.debug("CampanaNoEnEjecucion: %s", campana.id)
                    try:
                        del self.trackers_campana[campana]
                    except KeyError:
                        pass
                except NoMasContactosEnCampana:
                    # Esta excepcion es generada cuando la campaña esta
                    # en curso (el estado), pero ya no tiene pendientes
                    # FIXME: aca habria q' marcar la campana como finalizada?
                    # El tema es que puede haber llamadas en curso, pero esto
                    # no deberia ser problema...
                    self._banear_campana(campana)
                    logger.debug("NoMasContactosEnCampana: %s", campana.id)
                    try:
                        del self.trackers_campana[campana]
                    except KeyError:
                        pass

            try:
                self._update_trackers_campana()
            except NoHayCampanaEnEjecucion:
                logger.debug("No hay campanas en ejecucion. "
                    "Esperaremos %s segs.", self.espera_sin_campanas)
                time.sleep(self.espera_sin_campanas)


class Llamador(object):

    def __init__(self):
        self.rr_tracker = RoundRobinTracker()

    def run(self, max_loops=0):
        current_loop = 1
        for campana, id_contacto, numero in self.rr_tracker.generator():
            logger.debug("loop(): campana: %s - id_contacto: %s - numero: %s",
                campana, id_contacto, numero)

            procesar_contacto(campana, id_contacto, numero)

            current_loop += 1
            if max_loops > 0 and current_loop > max_loops:
                logger.info("max_loops alcanzado... saliendo...")
                return


#class CancelLoop(Exception):
#    """Excepcion usada para cancelar loop externo"""
#    pass
#
#
#class Llamador(object):
#
#    def _pendientes(self):
#        """Generador, devuelve datos para realizar llamadas"""
#
#        while True:
#            for campana in Campana.objects.obtener_ejecucion():
#                logger.info("Iniciando procesado de campana %s", campana.id)
#
#                # Chequeamos actuacion
#                actuacion = campana.obtener_actuacion_actual()
#                if not actuacion:
#                    logger.info("Cancelando xq no hay actuacion activa para "
#                        "campana %s", campana.id)
#                    continue
#
#                #
#                # Busca pendientes de campana siendo procesada y arranca
#                #
#
#                try:
#                    pendientes = EventoDeContacto.objects_gestion_llamadas.\
#                        obtener_pendientes(campana.id, 10)
#                    for pendiente in pendientes:
#
#                        # Fecha actual local.
#                        hoy_ahora = datetime.now()
#
#                        # Esto quiza no haga falta, porque en teoria
#                        # el siguiente control de actuacion detectara el
#                        # cambio de dia, igual hacemos este re-control
#                        if not campana.verifica_fecha(hoy_ahora):
#                            raise CancelLoop()
#
#                        if not actuacion.verifica_actuacion(hoy_ahora):
#                            raise CancelLoop()
#
#                        # Valida que la campana no se haya pausado.
#                        if Campana.objects.verifica_estado_pausada(
#                            campana.pk):
#                            raise CancelLoop()
#
#                        # Todo está OK. Generamos datos.
#                        id_contacto = pendiente[1]
#                        contacto = Contacto.objects.get(pk=id_contacto)
#                        yield campana, id_contacto, contacto.telefono
#
#                except CancelLoop:
#                    pass
#
#            else:
#                logger.debug("No hay campanas en ejecucion. Esperaremos...")
#                time.sleep(2)
#
#    def run(self, max_loops=0):
#        current_loop = 1
#        for campana, id_contacto, numero in self._pendientes():
#            logger.debug("loop(): campana: %s - id_contacto: %s - numero: %s",
#                campana, id_contacto, numero)
#            procesar_contacto(campana, id_contacto, numero)
#
#            current_loop += 1
#            if max_loops > 0 and current_loop > max_loops:
#                logger.info("max_loops alcanzado... saliendo...")
#                return


def main():
    logger.info("Iniciando loop: obteniendo campanas activas...")
    FTS_MAX_LOOPS = int(os.environ.get("FTS_MAX_LOOPS", "0"))
    Llamador().run(max_loops=FTS_MAX_LOOPS)


if __name__ == '__main__':
    main()
