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
from fts_daemon.asterisk_ami_http import AmiStatusTracker
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
    """Marca que la campaña en cuestion no está "en ejecucion",
    ya sea por el estado (ej: pausada), no esta en rango de fecha de campaña,
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

        self.loop__flag_limite_de_canales_alcanzado = False
        """Indica si es esta campana ha alcanzado el limite de canales"""

    def reset_loop_flags(self):
        """Resetea todas las variables y banderas de ROUND, o sea, las
        variables y banderas que son reseteadas antes de iniciar el ROUND
        """
        # Por ahora, solo una bandera
        self.loop__flag_limite_de_canales_alcanzado = False

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
        if not Campana.objects.verifica_estado_activa(self.campana.pk):
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


class RoundRobinTracker(object):

    def __init__(self):
        self.trackers_campana = {}
        """dict(): Campana -> CampanaTracker"""

        self.ami_status_tracker = AmiStatusTracker()
        """Status tracker via HTTP AMI"""

        self.ban_manager = BanManager()
        """Administrador de baneos"""

        # Quiza esto deberia estar en `self.trackers_campana`
        self._ultimo_refresco_trackers = datetime.now() - timedelta(days=30)
        """Ultima vez q' se consulto la BD, para refrescar los
        trackers. Es usado por necesita_refrescar_trackers() y
        refrescar_trackers()
        """

        # Quiza esto deberia estar en `self.ami_status_tracker`
        self._ultimo_refresco_ami_status = datetime.now() - timedelta(days=30)
        """Ultima vez q' se ejecuto *ŝtatus* via AMI HTTP."""

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

        Se crean instancias de CampanaTracker SOLO para las nuevas campañas.
        Las instancias de CampanaTracker para campañas que ya están siendo
        traqueadas con mantenidas. Las instancias de CampanaTracker de campañas
        que ya no son más trackeadas, son eliminadas.

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

    def necesita_refrescar_channel_status(self):
        if not self.trackers_campana:
            logger.debug("necesita_refrescar_channel_status(): no actualizamos"
                " porque no hay self.trackers_campana")
            return False

        flags_limite_de_canales_alcanzado = [
            tracker.loop__flag_limite_de_canales_alcanzado
                for tracker in self.trackers_campana.values()]

        if True not in flags_limite_de_canales_alcanzado:
            logger.debug("necesita_refrescar_channel_status(): no actualizamos"
                " porque no se alcanzo el limite en ninguna campaña")
            return False

        delta = datetime.now() - self._ultimo_refresco_ami_status
        # No hacemos más de 1 consulta cada 3 segundos
        if delta.days == 0 and delta.seconds < 3:
            logger.debug("necesita_refrescar_channel_status(): no actualizamos"
                " porque la ultima actualizacion fue recientemente")
            return False

        logger.debug("necesita_refrescar_channel_status(): True")
        return True

    def refrescar_channel_status(self):
        """Refresca `llamadas_en_curso_aprox` de `self.trackers_campana`,
        en caso que sea necesario y conveniente.

        En caso de error, no actualiza ningun valor.
        """
        #======================================================================
        # Chequeamos si realmente hace falta
        #======================================================================

        #======================================================================
        # SI hace falta!
        #======================================================================

        # Dict con campañas trackeadas
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
                logger.info("refrescar_channel_status(): "
                    "Ignorando datos de campana %s (%s llamadas en curso)",
                    campana.id, len(info_de_llamadas))

        # En este punto, campana_by_id tiene las campañas cuyos datos
        #  no fueron refrescados...
        for campana in campana_by_id.values():
            # FIXME: esto que hacemos aca, no es algo peligroso? Y si habia
            # en ejecucion!? Quizá deberiamos, además de este control, llevar
            # control de la cantidad de llamadas generadas por minuto
            logger.info("refrescar_channel_status(): no se recibieron "
                "datos para la campana %s... Suponemos que no hay "
                "llamadas en curso para dicha campana", campana.id)
            tracker = self.trackers_campana[campana]
            tracker.llamadas_en_curso_aprox = 0

    def onNoHayCampanaEnEjecucion(self):
        """Ejecutado por generator() cuando se detecta
        NoHayCampanaEnEjecucion.
        """
        logger.debug("No hay campanas en ejecucion.")

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
        """Ejecutado por generator() cuando se detecta
        LimiteDeCanalesAlcanzadoError. Esto implica que la campana que se
        estaba teniendo en cuenta debe ignorarse por esta vez, ya que
        ya se la colmado el límite de llamadas concurrentes.
        """
        logger.debug("onLimiteDeCanalesAlcanzadoError: %s", campana.id)

    def onNoSeDevolvioContactoEnRoundActual(self):
        """Ejecutado por generator() cuando se corrió el loop, pero no se
        devolvio ningun contacto.

        Las razones por las que no se proceso ningun contacto pueden ser
        variadas: no hay campañas en ejecución, se llegó al límite
        de canales por campaña, etc
        """
        logger.debug("onNoSeDevolvioContactoEnRoundActual(): "
            "No se procesaron contactos en esta iteracion.")

    def sleep(self, segundos):
        """Wrapper de time.sleep()"""
        time.sleep(segundos)

    def generator(self):
        """Devuelve los datos de contacto a contactar, de a una
        campaña por vez.

        :returns: (campana, contacto_id, telefono)
        """

        try:
            self.refrescar_trackers()
        except NoHayCampanaEnEjecucion:
            pass

        while True:

            ##
            ## Arrancamos un "round"
            ##

            loop__campanas_procesadas = 0

            # Trabajamos en copia, por si hace falta modificarse
            dict_copy = dict(self.trackers_campana)

            for campana, tracker in dict_copy.iteritems():
                tracker.reset_loop_flags()
                try:
                    yield tracker.next()
                    loop__campanas_procesadas += 1
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
                    tracker.loop__flag_limite_de_canales_alcanzado = True
                    self.onLimiteDeCanalesAlcanzadoError(campana)

            ##
            ## A esta altura ya terminamos de ejecutar el "round",
            ##    ahora chequeamos algunas condiciones
            ##

            if loop__campanas_procesadas == 0:
                self.onNoSeDevolvioContactoEnRoundActual()

            # Actualizamos lista de trackers, si corresponde
            if self.necesita_refrescar_trackers():
                try:
                    self.refrescar_trackers()
                except NoHayCampanaEnEjecucion:
                    self.onNoHayCampanaEnEjecucion()

            if not bool(self.trackers_campana):
                # No hay trabajo! Esperamos y hacemos `continue`
                # +------------------------------------------------------------
                # | Los eventos que deberian despertar este 'sleep' son:
                # | 1. campaña des-pausada
                # | 2. campaña entra en curso (por fecha u hora de actuacion)
                # | 3. campaña creada
                # +------------------------------------------------------------
                logger.debug("No hay trabajo. Esperamos %s segs. y luego "
                    "hacemos continue (reiniciamos ROUND)",
                    settings.FTS_DAEMON_SLEEP_SIN_TRABAJO)
                self.sleep(settings.FTS_DAEMON_SLEEP_SIN_TRABAJO)

                # No importa q' no se refresque el status via ami, total,
                #    no hay trabajo!
                continue

            # Si llegamos aca es porque tenemos trabajo por hacer, pero
            # si TODAS las campañas han llegado al límite, no tiene seguido
            # hacer un busy wait... mejor esperamos
            # +----------------------------------------------------------------
            # | Los eventos que deberian despertar este 'sleep' son:
            # | 1. se ha finalizado la llamada de cualquiera de las
            # |    campañas q' habian llegado al limite
            # +----------------------------------------------------------------
            flags_limite_de_canales_alcanzado = [
                tracker.loop__flag_limite_de_canales_alcanzado
                    for tracker in self.trackers_campana.values()]

            if set(flags_limite_de_canales_alcanzado) == set([True]):
                logger.debug("Todas las campañas han llegado al límite. "
                    "Esperamos %s segs. y luego seguioms hasta terminar "
                    "este ROUND",
                    settings.FTS_DAEMON_SLEEP_LIMITE_DE_CANALES)
                self.sleep(settings.FTS_DAEMON_SLEEP_LIMITE_DE_CANALES)
                # *NO* hacemos `continue`! Necesitamos refrescar el status
                #     de los canales via AMI.
                # continue

            # Refresca status de conexiones, AL FINAL, así nos aseguramos
            # de actualizar las instancias de trackers creadas
            # por `necesita_refrescar_trackers()` (aunque esto no es TAN asi,
            # ya que el refresh reusa las intancias de tracker, por lo tanto,
            # si chequearamos el status via AMI ANTES del refresh, seria
            # lo mismo.

            # Pero es importante refrescarla al final, así, en el proximo ROUND
            # la información está actualizada.
            if self.necesita_refrescar_channel_status():
                self.refrescar_channel_status()


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
