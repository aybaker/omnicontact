# -*- coding: utf-8 -*-
"""
Daemon que busca pendientes y realiza envios.
"""

from __future__ import unicode_literals

import collections
from datetime import datetime, timedelta
import os
import random
import re
import time

from django.conf import settings
from fts_daemon.asterisk_ami_http import AsteriskHttpClient
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


class BanManager(object):
    """Gestiona baneo de campañas"""

    def __init__(self):
        self.campanas_baneadas = {}
        """dict(): Campana -> datetime (hasta el momento que esta
        baneado"""

    def get_timedelta_baneo(self):
        """Devuelve tiempo por default de baneo"""
        return timedelta(minutes=1)

    def banear_campana(self, campana):
        """Banea una campana"""
        self.campanas_baneadas[campana] = datetime.now() + \
            self.get_timedelta_baneo()

    def esta_baneada(self, campana):
        """Devuelve booleano indicando si la campana esta baneada"""
        try:
            baneada_hasta = self.campanas_baneadas[campana]
        except KeyError:
            # Campaña no existe, asi q' no esta baneada...
            return False

        # Existe! Chequeamos si todavia está vigente
        if datetime.now() < baneada_hasta:
            return True
        else:
            del self.campanas_baneadas[campana]
            return False


class AmiStatusTracker(object):

    REGEX = re.compile("^Local/([0-9]+)-([0-9]+)@FTS_local_campana_([0-9]+)")

    def __init__(self):
        pass

    def _parse(self, calls_dicts):
        """
        Devuelve:
        1. dict, cuyo key es un string, con 3 elementos, separados por
           espacios: [contacto_id, numero, campana_id], y el
           valor es la lista de registros asociados a este key
        2. lista, con registros no parseados
        """
        parseados = collections.defaultdict(lambda: list())
        no_parseados = []
        for item in calls_dicts:
            if "channel" in item:
                # Local/28-620@FTS_local_campana
                match_obj = AmiStatusTracker.REGEX.match(item["channel"])
                if match_obj:
                    contacto_id = match_obj.group(1)
                    numero = match_obj.group(2)
                    campana_id = match_obj.group(3)
                    key = " ".join([contacto_id, numero, campana_id])
                    parseados[key].append(item)
                else:
                    no_parseados.append(item)
            else:
                no_parseados.append(item)
        return parseados, no_parseados

    def get_status_por_campana(self):
        """Devuelve diccionario, cuyos KEYs son los ID de campana,
        y VALUEs son listas. Cada lista es una lista con:
        [contacto_id, numero, campana_id]
        """

        # FIXME: crear cliente, loguear y reutilizar!
        client = AsteriskHttpClient()
        client.login()
        client.ping()
        calls_dicts = client.get_status().calls_dicts
        parseados, no_parseados = self._parse(calls_dicts)
        if no_parseados:
            logger.warn("Algunos registros no fueron parseados: %s registros",
                len(no_parseados))

        campanas = collections.defaultdict(lambda: list())
        for key in parseados:
            contacto_id, numero, campana_id = key.split()
            campanas[int(campana_id)].append([
                int(contacto_id), numero, int(campana_id)
            ])

        return campanas


class RoundRobinTracker(object):

    def __init__(self):
        self.trackers_campana = {}
        """dict(): Campana -> CampanaTracker"""

        self.ban_manager = BanManager()
        """Administrador de baneos"""

        self.espera_sin_campanas = 2
        """Cuantos segundos esperar si la consulta a la BD
        no devuelve ninguna campana activa"""

        self.espera_busy_wait = 1
        """Cuantos segundos esperar si en la ultima iteracion
        no se ha procesado ningún contacto. Esta espera es necesaria
        para evitar q' el daemon haga un 'busy wait'"""

        self._last_query_time = datetime.now() - timedelta(days=30)
        """Ultima vez q' se consulto la BD"""

    def necesita_refrescar_trackers(self):
        """Devuleve booleano, indicando si debe o no consultarse a
        la base de datos. Este metodo es ejecutado luego de cada
        intento de envio, por lo tanto es ejecutado muchas veces.

        Si devuelve 'True', se consultara la BD para actualizar
        la lista de campanas. Sino, se seguira utilizando la
        lista cacheada.

        En una futura implementación, además de utilizar un "timeout",
        podriamos chequear alguna variable que sea seteada
        asincronamente (ej: usando Redis), o podriamos conocer cuanto
        falta para que una campana se active (por fecha de la
        campaña o Actuacion).
        """
        # Quizá habria q' chequear más seguido si el server no
        # está haciendo nada, pero más espaciado si hay
        # llamadas en curso, no?
        delta = datetime.now() - self._last_query_time
        if delta.days > 0 or delta.seconds > 10:
            return True
        return False

    def refrescar_trackers(self):
        """Refresca la lista de trackers de campañas (self.trackers_campana),
        que incluye buscar en BD las campañas en ejecucion.

        Raises:
        - NoHayCampanaEnEjecucion
        """
        logger.debug("refrescar_trackers(): Iniciando...")
        self._last_query_time = datetime.now()
        old_trackers = dict(self.trackers_campana)
        new_trackers = {}
        for campana in Campana.objects.obtener_ejecucion():

            if self.ban_manager.esta_baneada(campana):
                logger.debug("La campana %s esta baneada", campana.id)
                continue

            if campana in old_trackers:
                # Ya existia de antes, la mantenemos
                new_trackers[campana] = old_trackers[campana]
                del old_trackers[campana]
            else:
                # Es nueva
                logger.debug("refrescar_trackers(): nueva campana: %s",
                    campana.id)
                new_trackers[campana] = CampanaTracker(campana)

        self.trackers_campana = new_trackers

        # Logueamos campanas q' no van mas...
        for campana in old_trackers:
            logger.info("refrescar_trackers(): quitando campana %s",
                campana.id)

        # Luego de procesar y loguear todo, si vemos q' no hay campanas
        # ejecucion, lanzamos excepcion
        if not self.trackers_campana:
            # No se encontraron campanas en ejecucion
            raise NoHayCampanaEnEjecucion()

    def onNoHayCampanaEnEjecucion(self):
        """Ejecutado por generator() cuando se detecta
        NoHayCampanaEnEjecucion.
        
        La implementación por default solo espera
        `self.espera_sin_campanas` segundos y retorna el control.
        """
        logger.debug("No hay campanas en ejecucion. "
            "Esperaremos %s segs.", self.espera_sin_campanas)
        time.sleep(self.espera_sin_campanas)
        # FIXME: aca se espera `espera_sin_campanas`, pero
        #  `necesita_refrescar_trackers()` usa otros tiempos...
        #  Seguramente deberiamos "unificar", ya q' para qué
        #   esperar '2 segudnos' si no se va a volver a chequear
        #  la BD hasta dentro de 10 segundos!?

    def onCampanaNoEnEjecucion(self, campana):
        """Ejecutado por generator() cuando se detecta
        CampanaNoEnEjecucion. Esto implica que la campana que se
        estaba por ejecutar, NO debio tenerse en cuenta.

        La implementación por default banea a la campana, y la
        elimina de `self.trackers_campana`
        """
        self.ban_manager.banear_campana(campana)
        logger.debug("onCampanaNoEnEjecucion: %s", campana.id)
        try:
            del self.trackers_campana[campana]
        except KeyError:
            pass

    def onNoMasContactosEnCampana(self, campana):
        """Ejecutado por generator() cuando se detecta
        NoMasContactosEnCampana. Esto implica que la campana que se
        estaba teniendo en cuenta en realidad no posee contactos
        a procesar

        La implementación por default banea a la campana, y la
        elimina de `self.trackers_campana`
        """
        logger.debug("onNoMasContactosEnCampana: %s", campana.id)
        self.ban_manager.banear_campana(campana)
        try:
            del self.trackers_campana[campana]
        except KeyError:
            pass

    def generator(self):
        """Devuelve datos de contacto a contactar:
        (campana, contacto_id, telefono)
        """
        while True:
            # Trabajamos en copia, por si hace falta modificarse
            contactos_procesados = 0
            dict_copy = dict(self.trackers_campana)
            for campana, tracker_campana in dict_copy.iteritems():
                try:
                    yield tracker_campana.next()
                    contactos_procesados += 1
                except CampanaNoEnEjecucion:
                    self.onCampanaNoEnEjecucion(campana)
                except NoMasContactosEnCampana:
                    # Esta excepcion es generada cuando la campaña esta
                    # en curso (el estado), pero ya no tiene pendientes
                    # FIXME: aca habria q' marcar la campana como finalizada?
                    # El tema es que puede haber llamadas en curso, pero esto
                    # no deberia ser problema...
                    self.onNoMasContactosEnCampana(campana)

            # Si no se procesaron contactos, esperamos 1 seg.
            if contactos_procesados == 0:
                logger.debug("No se procesaron contactos en esta iteracion. "
                    "Esperaremos %s seg.", self.espera_busy_wait)
                time.sleep(1)

            # Actualizamos lista de tackers
            if self.necesita_refrescar_trackers():
                try:
                    self.refrescar_trackers()
                except NoHayCampanaEnEjecucion:
                    self.onNoHayCampanaEnEjecucion()


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


def main(max_loop=0):
    logger.info("Iniciando loop: obteniendo campanas activas...")
    FTS_MAX_LOOPS = int(os.environ.get("FTS_MAX_LOOPS", max_loop))
    Llamador().run(max_loops=FTS_MAX_LOOPS)


if __name__ == '__main__':
    main()
