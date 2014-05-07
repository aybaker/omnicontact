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


class LimiteDeCanalesAlcanzadoError(Exception):
    """Se alcanzó el límite máximo de llamadas concurrentes que pude
    poseer una campana.
    """


class CampanaTracker(object):

    def __init__(self, campana):
        self.cache = []
        self.campana = campana
        self.actuacion = None
        # self.generator = None
        self.fetch_min = 20
        self.fetch_max = 100

        self._llamadas_en_curso_aprox = 0
        """Lleva un contador de las llamadas en curso aproximadas
        para esta campaña. Este valor es refrescado cada tanto con los
        datos devueltos por AsteriskHttpClient() (es ese momento no será
        aproximado, sino que será el valor cierto). Luego, con cada originate,
        incrementamos el contador en 1... lo que lo hace aproximado es que
        registramos las llamadas nuevas iniciadas, pero NO descontamos
        las llamadas finalizadas.

        ORIGINATE ASYNC: AsteriskHttpClient() devuelve informacion de las
        llamadas que todavia no fueron contestadas (en estado RINGING), por
        lo tanto, por lo tanto, nos da una visión bastante cierta de la
        cantidad de canales ocupados.
        """

    @property
    def llamadas_en_curso_aprox(self):
        return self._llamadas_en_curso_aprox

    @llamadas_en_curso_aprox.setter
    def llamadas_en_curso_aprox(self, value):
        logger.debug("Actualizando llamadas_en_curso_aprox, de %s a %s",
            self._llamadas_en_curso_aprox, value)
        assert type(value) == int
        self._llamadas_en_curso_aprox = value

    def _get_random_fetch(self):
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
            obtener_pendientes(self.campana.id, limit=self._get_random_fetch())

        if not contactos_values:
            raise NoMasContactosEnCampana()

        id_contacto_y_telefono = EventoDeContacto.objects_gestion_llamadas.\
            obtener_datos_de_contactos([tmp[1] for tmp in contactos_values])

        self.cache = [(self.campana, contacto_id, telefono)
            for contacto_id, telefono in id_contacto_y_telefono]

    def next(self):
        """Devuelve los datos de datos de contacto a contactar,
        para la campaña asociada a este tracker. Internamente, se encarga
        de obtener el generador, y obtener un dato.

        :returns: (campana, contacto_id, telefono)

        :raises: CampanaNoEnEjecucion
        :raises: NoMasContactosEnCampana
        """

        # Fecha actual local.
        hoy_ahora = datetime.now()

        # Esto quiza no haga falta, porque en teoria
        # el siguiente control de actuacion detectara el
        # cambio de dia, igual hacemos este re-control
        if not self.campana.verifica_fecha(hoy_ahora):
            raise CampanaNoEnEjecucion()

        if self._llamadas_en_curso_aprox >= self.campana.cantidad_canales:
            msg = ("Hay {0} llamadas en curso (aprox), y la campana "
                "tiene un limite de {1}").format(
                    self._llamadas_en_curso_aprox,
                    self.campana.cantidad_canales)
            raise LimiteDeCanalesAlcanzadoError(msg)

        #if not self.actuacion.verifica_actuacion(hoy_ahora):
        #    raise CampanaNoEnEjecucion()

        # Valida que la campana esté en estado valido
        if Campana.objects.verifica_estado_en_ejecucion(self.campana.pk):
            raise CampanaNoEnEjecucion()

        if not self.cache:
            self._populate_cache()  # -> NoMasContactosEnCampana

        self._llamadas_en_curso_aprox += 1
        return self.cache.pop(0)


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

        self.ami_status_tracker = AmiStatusTracker()
        """Status tracker via HTTP AMI"""

        self.ban_manager = BanManager()
        """Administrador de baneos"""

        self.espera_sin_campanas = 2
        """Cuantos segundos esperar si la consulta a la BD
        no devuelve ninguna campana activa"""

        self.espera_busy_wait = 1
        """Cuantos segundos esperar si en la ultima iteracion
        no se ha procesado ningún contacto. Esta espera es necesaria
        para evitar q' el daemon haga un 'busy wait'"""

        # Quiza esto deberia estar en `self.trackers_campana`
        self._ultimo_refresco_trackers = datetime.now() - timedelta(days=30)
        """Ultima vez q' se consulto la BD, para refrescar los
        trackers. Es usado por necesita_refrescar_trackers() y
        refrescar_trackers()
        """

        # Quiza esto deberia estar en `self.ami_status_tracker`
        self._ultimo_refresco_ami_status = datetime.now() - timedelta(days=30)
        """Ultima vez q' se ejecuto *ŝtatus* via AMI HTTP."""

        self.loop__limite_de_canales_alcanzado = False
        """Variable de 'loop' (o sea, seteada y usada en el
        loop de generator()"""

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
        delta = datetime.now() - self._ultimo_refresco_trackers
        if delta.days > 0 or delta.seconds > 10:
            return True
        return False

    def refrescar_trackers(self):
        """Refresca la lista de trackers de campañas (self.trackers_campana),
        que incluye buscar en BD las campañas en ejecucion.

        :raises: NoHayCampanaEnEjecucion
        """
        logger.debug("refrescar_trackers(): Iniciando...")
        self._ultimo_refresco_trackers = datetime.now()
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

    def refrescar_ami_si_corresponde(self):
        """Refresca `llamadas_en_curso_aprox` de `self.trackers_campana`,
        en caso que sea necesario y conveniente.

        Si self.loop__limite_de_canales_alcanzado no está seteado, entonces
        no es necesario.

        Si se refrescó hace menos de 3 segundos, entonces, no es conveniente.

        En caso de error, no actualiza ningun valor.
        """
        if not self.loop__limite_de_canales_alcanzado:
            logger.debug("refrescar_ami_si_corresponde(): no actualizamos"
                "porque no se alcanzo ningun limite")
            return

        if not self.trackers_campana:
            logger.debug("refrescar_ami_si_corresponde(): no actualizamos"
                "porque no hay self.trackers_campana")
            return

        delta = datetime.now() - self._ultimo_refresco_ami_status
        # No hacemos más de 1 consulta cada 3 segundos
        if delta.days == 0 and delta.seconds < 3:
            logger.debug("refrescar_ami_si_corresponde(): no actualizamos"
                "porque la ultima actualizacion fue recientemente")
            return

        campana_by_id = dict([(c.id, c) for c in self.trackers_campana])

        logger.info("Actualizando status via AMI HTTP")
        try:
            status = self.ami_status_tracker.get_status_por_campana()
        except:
            self._ultimo_refresco_ami_status = datetime.now()
            logger.exception("Error detectado al ejecutar "
                "ami_status_tracker.get_status_por_campana(). Los statuses "
                "no seran actualizados")
            return

        for campana_id, info_de_llamadas in status:
            campana = campana_by_id.get(campana_id, None)
            if campana:
                tracker = self.trackers_campana[campana]
                tracker.llamadas_en_curso_aprox = len(info_de_llamadas)
                del campana_by_id[campana]
            else:
                logger.info("refrescar_ami_si_corresponde(): "
                    "Ignorando datos de campana %s (%s llamadas en curso)",
                    campana.id, len(info_de_llamadas))

        # En este punto, campana_by_id tiene las campañas cuyos datos
        #  no fueron refrescados...
        for campana in campana_by_id:
            # FIXME: esto que hacemos aca, no es algo peligroso? Y si habia
            # en ejecucion!? Quizá deberiamos, además de este control, llevar
            # control de la cantidad de llamadas generadas por minuto
            logger.info("refrescar_ami_si_corresponde(): no se recibieron "
                "datos para la campana %s... Suponemos que no hay "
                "llamadas en curso para dicha campana", campana.id)
            tracker = self.trackers_campana[campana]
            tracker.llamadas_en_curso_aprox = 0

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

    def onLimiteDeCanalesAlcanzadoError(self, campana):
        logger.debug("onLimiteDeCanalesAlcanzadoError: %s", campana.id)
        self.loop__limite_de_canales_alcanzado = True

    def generator(self):
        """Devuelve datos de contacto a contactar:
        (campana, contacto_id, telefono)
        """
        while True:
            # Trabajamos en copia, por si hace falta modificarse
            contactos_procesados = 0

            ##
            ## Hacemos un "round"
            ##

            self.loop__limite_de_canales_alcanzado = False

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
                except LimiteDeCanalesAlcanzadoError:
                    self.onLimiteDeCanalesAlcanzadoError(campana)

            ##
            ## Finalizamos "round", ahora chequeamos algunas condiciones
            ##

            # Si no se procesaron contactos, esperamos 1 seg.
            if contactos_procesados == 0:
                logger.debug("No se procesaron contactos en esta iteracion. "
                    "Esperaremos %s seg.", self.espera_busy_wait)
                # TODO: unificar todas estas esperas en un solo lugar,
                # al final, o aprovechar de hacer otros procesamientos,
                # como finalizacoin de campanas...
                time.sleep(1)

            # Actualizamos lista de tackers
            if self.necesita_refrescar_trackers():
                try:
                    self.refrescar_trackers()
                except NoHayCampanaEnEjecucion:
                    self.onNoHayCampanaEnEjecucion()

            # Refresca status de conexiones, AL FINAL, así nos aseguramos
            # de actualizar las instancias de trackers creadas
            # por `necesita_refrescar_trackers()`
            # TODO: si no hay campañas en ejecución, arriba se esperará,
            # y luego se ejecutará el refresco de AMI... Esto no es un
            # problema, ya que de cualquier manera no hay nada que
            # refrescar, pero... ¿no seria mas correcto esperar al final?
            self.refrescar_ami_si_corresponde()


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
