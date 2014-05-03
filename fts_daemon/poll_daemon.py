# -*- coding: utf-8 -*-
'''
Created on Mar 27, 2014

@author: Horacio G. de Oro
'''

from __future__ import unicode_literals

import datetime
import os
import time

from django.conf import settings
from fts_daemon.asterisk_ami_http import AsteriskHttpOriginateError
from fts_web.models import Campana, EventoDeContacto, Contacto
from fts_web.utiles import get_class
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

    def _populate_cache(self):
        """Guarda datos a devolver en `self.cache`.

        Raises:
        - NoMasContactosEnCampana: si no hay mas llamados pendientes
        """
        if not self.campana.verifica_fecha(datetime.datetime.now()):
            raise CampanaNoEnEjecucion()

#        self.actuacion = self.campana.obtener_actuacion_actual()
#        if not self.actuacion:
#            logger.info("Cancelando xq no hay actuacion activa para "
#                "campana %s", self.campana.id)
#            raise CampanaNoEnEjecucion()

        contactos_values = EventoDeContacto.objects_gestion_llamadas.\
            obtener_pendientes(self.campana.id, 50)

        if not contactos_values:
            raise NoMasContactosEnCampana()

        contactos = [Contacto.objects.get(pk=tmp[1])
            for tmp in contactos_values]

        self.cache = [(self.campana, contacto.id, contacto.telefono)
            for contacto in contactos]

    def next(self):
        if self.generator is None:
            self.generator = self.get_generator()
        return next(self.generator)

    def get_generator(self):
        """Devuelve datos de contacto a contactar

        Raises:
        - CampanaNoEnEjecucion
        - NoMasContactosEnCampana
        """
        while True:

            # Fecha actual local.
            hoy_ahora = datetime.datetime.now()

            # Esto quiza no haga falta, porque en teoria
            # el siguiente control de actuacion detectara el
            # cambio de dia, igual hacemos este re-control
            if not self.campana.verifica_fecha(hoy_ahora):
                raise CampanaNoEnEjecucion()

#            if not self.actuacion.verifica_actuacion(hoy_ahora):
#                raise CampanaNoEnEjecucion()

            # Valida que la campana no se haya pausado.
            if Campana.objects.verifica_estado_pausada(self.campana.pk):
                raise CampanaNoEnEjecucion()

            if not self.cache:
                self._populate_cache()  # -> NoMasContactosEnCampana

            yield self.cache.pop(0)


class RoundRobinTracker(object):

    def __init__(self):
        self.trackers_campana = {}
        self.cache = []
        self.iter_count = 0
        self.espera_sin_campanas = 2

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
            if campana in old_trackers:
                # Ya existia de antes
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
                    try:
                        del self.trackers_campana[campana]
                    except KeyError:
                        pass
                except NoMasContactosEnCampana:
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
#                        hoy_ahora = datetime.datetime.now()
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


def procesar_contacto(campana, contacto_id, numero):
    """Intenta contactar"""

    logger.info("Realizando originate - campana: %s - contacto: %s",
        campana.id, contacto_id)

    EventoDeContacto.objects.inicia_intento(campana.id, contacto_id)

    # Local/{contactoId}-{numberToCall}@FTS_local_campana_{campanaId}
    channel = settings.ASTERISK['LOCAL_CHANNEL'].format(
        contactoId=str(contacto_id),
        numberToCall=str(numero),
        campanaId=str(campana.id),
    )
    context = campana.get_nombre_contexto_para_asterisk()
    exten = settings.ASTERISK['EXTEN'].format(
        contactoId=str(contacto_id),
    )

    http_client_clazz = get_class(settings.FTS_ASTERISK_HTTP_CLIENT)
    http_ami_client = http_client_clazz()

    try:
        http_ami_client.login()
        http_ami_client.originate(channel, context, exten, 1,
            (campana.segundos_ring + 2) * 1000, async=True)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_successful(
                campana.id, contacto_id)
    except AsteriskHttpOriginateError:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, contacto_id)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_failed(
                campana.id, contacto_id)
    except:
        logger.exception("Originate failed - campana: %s - contacto: %s",
            campana.id, contacto_id)
        EventoDeContacto.objects.\
            create_evento_daemon_originate_internal_error(
                campana.id, contacto_id)


def main():
    logger.info("Iniciando loop: obteniendo campanas activas...")
    FTS_MAX_LOOPS = int(os.environ.get("FTS_MAX_LOOPS", "0"))
    Llamador().run(max_loops=FTS_MAX_LOOPS)


if __name__ == '__main__':
    main()
